from pyo import *
from effects import *

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
        pyoArgsAssert(self, "s", mode)
        PyoObject.__init__(self)
        self._mode = mode.replace(' ', '')
        self._midiSetup()
        self._algoSelector()
        self._base_objs = self._output.getBaseObjects()

    def _midiSetup(self):
        """Initialize what concerns MIDI."""
        self._notes = Notein(scale=1, poly=32)
        self._notes.keyboard()
        self._freqs = self._notes["pitch"]
        self._amps = MidiAdsr(self._notes["velocity"])

    def _algoSelector(self):
        """Select the algorithm based on 'mode' attribute."""
        modeMethodName = '_' + self._mode
        algo = getattr(self, modeMethodName, None)
        
        # Checks if the algorithm exists and calls it the associated method
        if algo is not None and callable(algo):
            algo()
        else:
            raise ValueError(f"L'algoritmo specificato '{modeMethodName[1:]}' non esiste o non è eseguibile.")
          
    def _detuneGenerator(self, *detunes):
        """
        Create a list of Sig objects or None for provided detunes and Set instance variables for non-None detune_ctrls.

        :Args:

            *detunes: ints
                detunes values for each operator

        """
        detune_ctrls = [Sig(detune) if detune is not None else None for detune in detunes]
        for i, detune_ctrl in enumerate(detune_ctrls, start=1):
            if detune_ctrl is not None:
                setattr(self, f'_detune{i}', detune_ctrl)
        
    def _operatorGenerator(self, *ops):
        """
        This method take in input 6 lists (if fm) or str (if sin), one for each operator.

        :Args:

            *ops: lists [ratio, index] or 'sin'
                operator values.
            
        If there is a list, values are:

        :Args:

            ratio: int [1,64]
                A factor that, when multiplied by the carrier parameter, gives the modulator frequency.
            index: float [0,0.5]
                The modulation index. This value multiplied by the modulator frequency gives the modulator amplitude.
        """
        self._sinCount = 0
        self._fmCount = 0
        self._opSituation = []
        self._opList = [op if op is not None else None for op in ops]

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
  
    def _SinOrFM(self, obj: str, opNumber: int, ratio: int = None, index: float = None):
        """
        Create a sine or FM by also setting the detune level.

        :Args:

            obj: str ['fm' or 'sin']
                Object to create.
            opNumber: int [1, 6] 
                Operator opNumber.
            ratio: int [1,64]
                A factor that, when multiplied by the carrier parameter, gives the modulator frequency.
            index: float [0,0.5]
                The modulation index. This value multiplied by the modulator frequency gives the modulator amplitude.
        """
        detune_value = getattr(self, f'_detune{opNumber}')
        frequency = self._freqs * (2 ** (detune_value / 1200))
        if obj == 'fm':
            return FM(frequency, ratio, index, mul=self._adsrGenerator(self._fmCount+self._sinCount+1))
        return Sine(frequency, mul=self._adsrGenerator(self._fmCount+self._sinCount+1))

    def _adsrGenerator(self, opNumber: int):
        """
        Set ADSR of the operator specified. If there is a preset in the algo inizialize ADSR with those values

        :Args: 

            opNumber: int [1,6]
                Operator number.
        """
        try:
            if self._adsrPresets:
                preset = self._adsrPresets[opNumber-1]
                setattr(self, f'_adsr{opNumber}', MidiAdsr(self._notes["velocity"], attack=preset[0], decay=preset[1], sustain=preset[2], release=preset[3], mul=self._volumeGenerator(opNumber)))
        except AttributeError:
            setattr(self, f'_adsr{opNumber}', MidiAdsr(self._notes["velocity"],  mul=self._volumeGenerator(opNumber)))

        adsr = getattr(self, f'_adsr{opNumber}')
        adsr.ctrl(title=f'adsr {opNumber}')
        return adsr

    def _volumeGenerator(self, opNumber: int):
        """
        Set volume of the operator specified. If there is a preset in the algo inizialize volume with that value

        :Args: 

            opNumber: int [1,6]
                Operator number.
        """

        setattr(self, f'_volume{opNumber}', Sig(1))
        volume = getattr(self, f'_volume{opNumber}')
        try: 
            if self._volumePresets:
                volume.ctrl(map_list=[SLMap(0, 1, 'lin', 'value', self._volumePresets[opNumber-1])], title=f'Volume {opNumber}')
        except AttributeError:
            volume.ctrl(map_list=[SLMap(0, 1, 'lin', 'value', 1)], title=f'Volume {opNumber}')
        return volume

    def _countChecker(self):
        """Check if the actual number of operator is consistent."""
        count = self._sinCount + (2 * self._fmCount)
        if count >= 6:
            return False
        return True

    def _outputGenerator(self):
        """Sum all sounds genetared by operators and send it to out."""
        op_values = [getattr(self, f"_op{i}", 0) for i in range(1, 7)]
        self._output = Pan(sum(op_values[:self._fmCount + self._sinCount]))

    def _ctrlGenerator(self, *ops):
        self._parametersCtrl(ops)
        self._detunesCtrl(ops)

    def _parametersCtrl(self, ops):
        """Generate sliders for frequency control for each operator."""
        for i, op in enumerate(ops):
            if op == None: break
            if self._opSituation[i] == 'f':
                ratiomap = SLMap(1, 64, 'lin', 'ratio', op[0], 'int')
                indexmap = SLMap(0, 0.5, 'lin', 'index', op[1])
                getattr(self, f'_op{i + 1}').ctrl(map_list=[ratiomap, indexmap], title=f'Operator {i+1}')
    
    def _detunesCtrl(self, ops):
        """Generate sliders for detune control for each operator."""
        detune_ctrls = [getattr(self, f'_detune{i + 1}', None) for i in range(6)]
        for i, op in enumerate(ops):
            if detune_ctrls[i] is not None:
                detune_ctrls[i].ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', getattr(self, f'_ctrlDet{i + 1}', 0), 'int')], title=f'detune OP {i + 1}')
                
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
        self._output = Chorus(self._output)
        self._output = Freeverb(self._output)
        
    def _electricpiano(self):
        self._adsrPresets = [[0.031, 0.288, 0.408, 0.681],[0.035, 0.273, 0.385, 0.669],[0.023, 0.324, 0.419, 0.615]]
        self._volumePresets = [1, 0.73, 0.88]
        self._detuneGenerator(2, 0, 4)
        self._operatorGenerator([1, 0.060], [14, 0.010], [1, 0.023])
        self._outputGenerator()
        self._output = Freeverb(self._output)

    def _lead1(self):
        self._adsrPresets = [[0.031, 0.288, 0.408, 0.681],[0.035, 0.273, 0.385, 0.669],[0.023, 0.324, 0.419, 0.615]]
        self._volumePresets = [1, 0.73, 0.88]
        self._detuneGenerator(2, 0, 4)
        self._operatorGenerator([1, 0.060], [14, 0.010], [1, 0.023])
        self._outputGenerator()
        self._output = Compress(self._output, mul=3)
        self._output = Crunch(self._output)
        self._output = Freeverb(self._output)

    def _lead2(self):
        self._adsrPresets = [[0.031, 0.288, 0.408, 0.681],[0.035, 0.273, 0.385, 0.669],[0.023, 0.324, 0.419, 0.615]]
        self._volumePresets = [1, 0.73, 0.88]
        self._detuneGenerator(2, 0, 4)
        self._operatorGenerator([1, 0.060], [14, 0.010], [1, 0.023])
        self._outputGenerator()
        self._output = Compress(self._output, mul=3)
        self._output = Tube(self._output)

    def _lead3(self):
        self._adsrPresets = [[0.031, 0.288, 0.408, 0.681],[0.035, 0.273, 0.385, 0.669],[0.023, 0.324, 0.419, 0.615]]
        self._volumePresets = [1, 0.73, 0.88]
        self._detuneGenerator(2, 0, 4)
        self._operatorGenerator([1, 0.060], [14, 0.010], [1, 0.023])
        self._outputGenerator()
        self._output = Compress(self._output, mul=3)
        self._output = Bitcrush(self._output, 12)

    def _bass(self):
        self._adsrPresets = [[0.02, 0.02, 0.317, 0.1],[0.09, 0.233, 0.351, 0.1],[0.20, 0.234, 0.001, 0.1]]
        self._volumePresets = [1, 1, 1]
        self._detuneGenerator(0, 0, 0)
        self._operatorGenerator([16, 0.50], [14, 0.64], [6, 0.7])
        self._outputGenerator()
        self._output = MoogLP(self._output, 400)
        self._output = Disto(self._output,0.5)

    def _bass2(self):
        self._adsrPresets = [[0.031, 0.288, 0.408, 0.1],[0.035, 0.273, 0.385, 0.1],[0.023, 0.324, 0.419, 0.1]]
        self._volumePresets = [1, 0.73, 0.88]
        self._detuneGenerator(0, 0, 0)
        self._operatorGenerator([1, 0.060], [14, 0.010], [1, 0.023])
        self._outputGenerator()
        self._output = Compress(self._output, mul=3)
        self._output = Bitcrush(self._output, 8)        
        self._output = Zap(self._output)
        self._output = MoogLP(self._output, 400)

    def _pad1(self):
        self._adsrPresets = [[0.7, 0.6, 0.3, 0.6],[0.7, 0.6, 0.6, 0.6],[0.7, 0.6, 0.6, 0.6]]
        self._volumePresets = [0.8, 1, 1]
        self._detuneGenerator(0, 0, 0)
        self._operatorGenerator([1, 0.4], [3, 0.04], [1, 0.3])
        self._outputGenerator()
        self._output = Overdrive(self._output)
        self._output = Chorus(self._output)
        self._output = MoogLP(self._output, 2000)
        self._output = Freeverb(self._output, 0.7 ,1, 0.5)

    def _pad2(self):
        self._adsrPresets = [[0.7, 0.6, 0.3, 0.6],[0.7, 0.6, 0.6, 0.6],[0.7, 0.6, 0.6, 0.6]]
        self._volumePresets = [0.8, 1, 1]
        self._detuneGenerator(0, 0, 0)
        self._operatorGenerator([1, 0.4], [3, 0.04], [1, 0.3])
        self._outputGenerator()
        self._output = Disto(self._output,0.5)
        self._output = Chorus(self._output)
        self._output = MoogLP(self._output, 2000)
        self._output = Freeverb(self._output, 0.7 ,1, 0.5)

if __name__ == '__main__':
    s = Server().boot()
    s.setAmp(0.1)

    a = DX7('pad1').out()
    a.ctrl()
    Spectrum(a)

    s.gui(locals())
