from pyo import *
from PIL import Image


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

    def __init__(self, mode: str = '6'):
        PyoObject.__init__(self, 1, 0)
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
        notes = Notein(scale=1, poly=32)

        # Attiva la tastiera virtuale per l'input MIDI.
        notes.keyboard()

        # Memorizza le frequenze delle note ricevute in self._freqs.
        self._freqs = notes["pitch"]

        # Crea un oggetto Port per gestire l'ampiezza (dinamica) delle note in base alla velocità.
        self._amps = MidiAdsr(notes["velocity"])

        # Crea un controllo (slider) per regolare in tempo reale gli attacchi e i rilasci delle note.
        self._amps.ctrl(title='Attack and Release')

    def _volumeGenerator(self, op):
        # Crea una variabile di istanza per il volume dell'operatore specificato.
        setattr(self, f'_volume{op}', Sig(1))

        # Configura il controllo (slider) per il volume dell'operatore.
        volume = getattr(self, f'_volume{op}')
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

            setattr(self, f"_op{i}", op_instance * self._volumeGenerator(i))
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

    def _ctrlGenerator(self, *ops):
        # Titoli dei parametri degli operatori
        param_titles = ['Operator 1', 'Operator 2', 'Operator 3', 'Operator 4', 'Operator 5', 'Operator 6']

        # Lista di controlli di detune per ciascuna corda, ottenuti dagli attributi self._detune1, self._detune2, ecc.
        detune_ctrls = [getattr(self, f'_detune{i + 1}', None) for i in range(6)]

        # Itera attraverso gli operatori passati come argomenti variabili
        for i, op in enumerate(ops):
            # Controlla se l'indice i è valido e se l'operatore corrispondente è abilitato ('f' indica attivo)
            if i < len(self._opSituation) and self._opSituation[i] == 'f':
                # Configura le mappe di controllo per il rapporto di frequenza (ratiomap) e l'indice (indexmap) dell'operatore corrente
                ratiomap = SLMap(1, 64, 'lin', 'ratio', op[0], 'int')
                indexmap = SLMap(0, 0.5, 'lin', 'index', op[1])
                
                # Applica le mappe di controllo agli attributi dell'operatore corrente utilizzando il metodo .ctrl()
                getattr(self, f'_op{i + 1}').ctrl(map_list=[ratiomap, indexmap], title=param_titles[i])

            # Controlla se l'indice i è valido, se l'operatore corrispondente è abilitato e se esiste un controllo di detune per l'operatore
            if i < len(self._opSituation) and self._opSituation[i] is not None and detune_ctrls[i] is not None:
                # Configura la mappa di controllo per il valore del detune dell'operatore corrente
                detune_ctrls[i].ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', getattr(self, f'_ctrlDet{i + 1}', 0), 'int')], title=f'detune OP {i + 1}')

    def _outputGenerator(self):
        # Ottieni i valori degli operatori 1-6 dalla classe.
        op_values = [getattr(self, f"_op{i}", 0) for i in range(1, 7)]

        # Calcola l'output sommando i valori degli operatori selezionati (dai primi 0 a fmCount + sinCount - 1).
        self._output = sum(op_values[:self._fmCount + self._sinCount])

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
            return FM(frequency, ratio, index, mul=self._amps)
        return Sine(frequency, mul=self._amps)

    @staticmethod
    def _getLayout(image):
        image = Image.open(image)
        resized_image = image.resize((200, 200))
        resized_image.show()

    def play(self, dur=0, delay=0):
        self._output.play(dur, delay)
        return self

    def stop(self, wait=0):
        self._output.stop(wait)
        return self

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output = Pan(self._output)
        self._output = Freeverb(self._output)
        self._output.ctrl(title='Reverb')
        self._output.out(chnl, inc, dur, delay)
        return self

    def ctrl(self):
        self._ctrlGenerator(*self._opList)

    def __repr__(self):
        return super().__repr__()

# ----- DEFAULT ALGORITHMS ----- #

    def _29(self):
        #self._getLayout('./Images/algoTwentynine.png')
        self._detuneGenerator(0, 0, 0, 0)
        self._operatorGenerator([1, 0], [1, 0], 'sin', 'sin')
        self._outputGenerator()

    def _6(self):
        #self._getLayout('./Images/algoSix.png')
        self._detuneGenerator(0, 0, 0)
        self._operatorGenerator([1, 0], [1, 0], [1, 0])
        self._outputGenerator()

    def _bell(self):
        #self._getLayout('./Images/algoTwentynine.png')
        self._detuneGenerator(2, 6, -13, -7)
        self._operatorGenerator([13, 0.371], [31, 0.188], 'sin', 'sin')
        self._outputGenerator()

    def _electricpiano(self):
        #self._getLayout('./Images/algoSix.png')
        self._detuneGenerator(-3, 0, 7)
        self._operatorGenerator([1, 0.060], [14, 0.004], [1, 0.023])
        self._outputGenerator()
    
    def _user(self):
        print('\n--- Step 1 ---\nYou have to decide FM operators number. Please note that DX7 has 6 operators and FM operator worth for two because is implicit that a sin operator modules each one.')
        fmop = int(input('Insert number of FM operators (max 3): '))

        print('\n--- Step 2 ---\nNumber of master operators: {}\nNumber of sin operators: {}'.format(6-fmop, 6-2*fmop))
        detunes = input('Now insert for each master operator the level of initial detuning between -15 and 15 (ex. 3 -6 7): ')
        detunes = detunes.split()
        if len(detunes) != (6 - fmop):
            raise OperatorNumberError('Something went wrong with operators number.')
        detunes = list(map(int, detunes))
        self._detuneGenerator(*detunes)

        print('\n--- Step 3 ---\nYou have now to decide ratio and index for every fm operator.')
        print("Insert ratio between 1 and 64 and index between 0 and 0.5 if you want a fm operator or 'sin' if you want a sin operator. Do that for all master operator (ex. 12 0.345.\n")
        ops = []
        for x in range(1,7):
            if x > (6 - fmop): break
            op = input("Operator {}: ".format(x))

            if op != 'sin':
                op = op.split()
                op = list(map(float, op))
            ops.append(op)
        self._operatorGenerator(*ops)
        
        self._outputGenerator()

# ----- USER ALGORITHMS ----- #

# ----- TEST CODE ----- #

if __name__ == '__main__':
    s = Server().boot()
    s.setAmp(0.1)

    a = DX7('electric piano').out()
    a.ctrl()

    
    Spectrum(a)

    s.gui(locals())
