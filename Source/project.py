from pyo import *

class ImplementationError(Exception):
    pass

class OperatorNumberError(Exception):
    pass

class DX7(PyoObject):
    """
    This class provides a simple emulation of the famous Yamaha DX7.

    :Parent: :py:class:`PyoObject`

    :Args:

        mode: str, optional
            algorithm or preset of DX7. Defaults to 6.

    >>> s = Server().boot()
    >>> s.setAmp(0.1)
    >>> a = DX7('6').out()
    >>> Spectrum(a)
    >>> s.gui(locals())
    """

    def __init__(self, mode: str = 'electric piano'):
        PyoObject.__init__(self)

        if not isinstance(mode, str):
            raise TypeError('mode must be string')
        self._mode = mode.replace(' ', '')

        self._midiSetup()
        self._algoSelector()

        self._base_objs = self._output.getBaseObjects()

    def _algoSelector(self):
        # Seleziona l'algoritmo in base alla modalità
        modeMethodName = '_' + self._mode
        algo = getattr(self, modeMethodName, None)
        
        # Se l'algoritmo esiste e può essere chiamato, eseguilo
        if algo is not None and callable(algo):
            algo()
        else:
            # Altrimenti, solleva un'eccezione con un messaggio di errore personalizzato
            raise ValueError(f"L'algoritmo specificato '{modeMethodName}' non esiste o non è eseguibile.")

    def _midiSetup(self):
        # Inizializza l'oggetto Notein per ricevere messaggi MIDI sulle note e velocità.
        self._notes = Notein(scale=1, poly=32)

        # Attiva la tastiera virtuale per l'input MIDI.
        self._notes.keyboard()

        # Memorizza le frequenze delle note ricevute in self._freqs.
        self._freqs = self._notes["pitch"]

        # Crea un oggetto Port per gestire l'ampiezza (dinamica) delle note in base alla velocità.
        self._amps = MidiAdsr(self._notes["velocity"])

    def _adsrGenerator(self, op):
        # Crea una variabile di istanza per il volume dell'operatore specificato.
        try:
            if self._adsrPresets:
                preset = self._adsrPresets[op-1]
                setattr(self, f'_adsr{op}', MidiAdsr(self._notes["velocity"], attack=preset[0], decay=preset[1], sustain=preset[2], release=preset[3], mul=self._volumeGenerator(op)))
        except AttributeError:
            setattr(self, f'_adsr{op}', MidiAdsr(self._notes["velocity"],  mul=self._volumeGenerator(op)))

        adsr = getattr(self, f'_adsr{op}')
        adsr.ctrl(title=f'adsr {op}')
        return adsr

    def _volumeGenerator(self, op):
        # Crea una variabile di istanza per il volume dell'operatore specificato.
        setattr(self, f'_volume{op}', Sig(1))

        # Configura il controllo (slider) per il volume dell'operatore.
        volume = getattr(self, f'_volume{op}')
        try: 
            if self._volumePresets:
                volume.ctrl(map_list=[SLMap(0, 1, 'lin', 'value', self._volumePresets[op-1])], title=f'Volume {op}')
        except AttributeError:
            volume.ctrl(map_list=[SLMap(0, 1, 'lin', 'value', 1)], title=f'Volume {op}')
        return volume
        
    def _operatorGenerator(self, op1=None, op2=None, op3=None, op4=None, op5=None, op6=None):
        """
        This method take in input 6 lists (if fm) or str (if sin), one for each operator. The lists contain in this exact order:

            ratio: int [1,64]
                A factor that, when multiplied by the carrier parameter, gives the modulator frequency.
            index: float [0,0.5]
                The modulation index. This value multiplied by the modulator frequency gives the modulator amplitude.
        """

        self._sinCount, self._fmCount = 0, 0
        self._opSituation = []
        self._opList = [op1, op2, op3, op4, op5, op6]

        for i, op in enumerate(self._opList, start=1):
            if isinstance(op, str):
                op_instance = self._SinOrFM('sin', str(i))
                self._sinCount += 1
                self._opSituation.append('s')
            else:
                op_instance = self._SinOrFM('fm', str(i), op[0], op[1])
                self._fmCount += 1
                self._opSituation.append('f')

            setattr(self, f"_op{i}", op_instance)
            if not self._countChecker(): break
          
    def _detuneGenerator(self, *detunes):
        # Crea una lista vuota di controlli di detune per ogni corda (6 corde in totale).
        detune_ctrls = [None] * 6

        # Itera attraverso gli argomenti detunes (detune passati come argomenti variabili).
        # Crea controlli Sig solo per i valori detune non None e li assegna agli attributi self._ctrlDet1, self._ctrlDet2, ecc.
        for i, detune in enumerate(detunes):
            if detune is not None:
                detune_ctrls[i] = Sig(detune)
                setattr(self, f'_ctrlDet{i + 1}', detune)

        # Assegna i controlli di detune creati ai relativi attributi self._detune1, self._detune2, ecc.
        self._detune1, self._detune2, self._detune3, self._detune4, self._detune5, self._detune6 = detune_ctrls

    def _parametersCtrl(self, ops):
        for i, op in enumerate(ops):
            if op == None: break
            if self._opSituation[i] == 'f':
                ratiomap = SLMap(1, 64, 'lin', 'ratio', op[0], 'int')
                indexmap = SLMap(0, 0.5, 'lin', 'index', op[1])
                getattr(self, f'_op{i + 1}').ctrl(map_list=[ratiomap, indexmap], title=f'Operator {i+1}')
    
    def _detunesCtrl(self, ops):
        detune_ctrls = [getattr(self, f'_detune{i + 1}', None) for i in range(6)]
        for i, op in enumerate(ops):
            if detune_ctrls[i] is not None:
                detune_ctrls[i].ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', getattr(self, f'_ctrlDet{i + 1}', 0), 'int')], title=f'detune OP {i + 1}')
                
    def _ctrlGenerator(self, *ops):
        self._parametersCtrl(ops)
        self._detunesCtrl(ops)

    def _outputGenerator(self):
        # Ottieni i valori degli operatori 1-6 dalla classe.
        op_values = [getattr(self, f"_op{i}", 0) for i in range(1, 7)]

        # Calcola l'output sommando i valori degli operatori selezionati (dai primi 0 a fmCount + sinCount - 1).
        self._output = Pan(sum(op_values[:self._fmCount + self._sinCount]))

    def _countChecker(self):
        # Calcola il numero totale di operatori combinando il numero di operatori sinusoidali (self._sinCount) e operatori FM doppi (2*self._fmCount).
        count = self._sinCount + (2 * self._fmCount)

        # Controlla se il numero totale di operatori supera 6 (limite massimo per il sintetizzatore DX7).
        if count >= 6:
            return False
        return True

    def _SinOrFM(self, obj, number, ratio=None, index=None):
        # Ottieni il valore di detune per l'operatore corrente (numero).
        detune_value = getattr(self, f'_detune{number}')

        # Calcola la frequenza tenendo conto del valore di detune (in centesimi).
        frequency = self._freqs * (2 ** (detune_value / 1200))

        # Crea un oggetto FM o Sine in base al parametro obj.
        # Utilizza la frequenza calcolata e il valore di ampiezza (self._amps) per il controllo della dinamica.
        if obj == 'fm':
            return FM(frequency, ratio, index, mul=self._adsrGenerator(self._fmCount+self._sinCount+1))
        return Sine(frequency, mul=self._adsrGenerator(self._fmCount+self._sinCount+1))

    def play(self, dur=0, delay=0):
        self._output.play(dur, delay)
        return self

    def stop(self, wait=0):
        self._output.stop(wait)
        return self

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output.out(chnl, inc, dur, delay)
        return self

    def ctrl(self):
        self._ctrlGenerator(*self._opList)

    def __repr__(self):
        return super().__repr__()

# ----- ALGORITHMS ----- #

    def _bell(self):
        self._adsrPresets = [[0.010, 0.050, 0.700, 0.7],[0.010, 0.050, 0.700, 0.7],[0.010, 0.050, 0.700, 0.7],[0.010, 0.050, 0.700, 0.7]]
        self._detuneGenerator(2, 6, -13, -7)
        self._operatorGenerator([13, 0.371], [31, 0.188], 'sin', 'sin')
        self._outputGenerator()
        self._output = MoogLP(self._output, 10000)
        self._output = Delay1(self._output)
        self._output = Chorus(self._output)
        self._output = Freeverb(self._output)
        
    def _electricpiano(self):
        self._adsrPresets = [[0.031, 0.288, 0.408, 0.681],[0.035, 0.273, 0.385, 0.669],[0.023, 0.324, 0.419, 0.615]]
        self._volumePresets = [1, 0.73, 0.88]
        self._detuneGenerator(2, 0, 4)
        self._operatorGenerator([1, 0.060], [14, 0.010], [1, 0.023])
        self._outputGenerator()
        self._output = Freeverb(self._output)

    def _bass(self):
        self._adsrPresets = [[0.02, 0.02, 0.317, 0.1],[0.09, 0.233, 0.351, 0.1],[0.20, 0.234, 0.001, 0.1]]
        self._volumePresets = [1, 1, 1]
        self._detuneGenerator(0, 0, 0)
        self._operatorGenerator([16, 0.50], [14, 0.64], [6, 0.7])
        self._outputGenerator()
        self._output = MoogLP(self._output, 400)
        self._output = Disto(self._output,0.5)

    def _pad(self):
        self._adsrPresets = [[0.7, 0.6, 0.3, 0.6],[0.7, 0.6, 0.6, 0.6],[0.7, 0.6, 0.6, 0.6]]
        self._volumePresets = [0.8, 1, 1]
        self._detuneGenerator(0, 0, 0)
        self._operatorGenerator([1, 0.4], [3, 0.04], [1, 0.3])
        self._outputGenerator()
        self._output = Disto(self._output,1)
        self._output = Chorus(self._output)
        self._output = MoogLP(self._output, 2000)
        self._output = Freeverb(self._output, 0.7 ,1, 0.5)

if __name__ == '__main__':
    s = Server().boot()
    s.setAmp(0.1)

    a = DX7('bell').out()


    Spectrum(a)

    s.gui(locals())
