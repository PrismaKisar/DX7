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
        algo = getattr(self, '_' + self._mode, None)
        if algo is not None and callable(algo):
            algo()
        else:
            print("Il metodo specificato non esiste o non è eseguibile.")

    def _midiSetup(self):
        notes = Notein(scale=1, poly=32)
        notes.keyboard()
        self._freqs = notes["pitch"]
        self._amps = Port(notes["velocity"], risetime=0.005, falltime=0.2)
        self._amps.ctrl(title='Attack and Release')

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

        if isinstance(op1, str):
            self._op1 = self._SinOrFM('sin', '1')
            self._sinCount += 1
            self._opSituation.append('s')
        elif isinstance(op1, list):
            self._op1 = self._SinOrFM('fm', '1', op1[0], op1[1])
            self._fmCount += 1
            self._opSituation.append('f')

        if isinstance(op2, str):
            self._op2 = self._SinOrFM('sin', '2')
            self._sinCount += 1
            self._opSituation.append('s')
        elif isinstance(op2, list):
            self._op2 = self._SinOrFM('fm', '2', op2[0], op2[1])
            self._fmCount += 1
            self._opSituation.append('f')

        if isinstance(op3, str):
            self._op3 = self._SinOrFM('sin', '3')
            self._sinCount += 1
            self._opSituation.append('s')
        elif isinstance(op3, list):
            self._op3 = self._SinOrFM('fm', '3', op3[0], op3[1])
            self._fmCount += 1
            self._opSituation.append('f')

        if isinstance(op4, str):
            self._op4 = self._SinOrFM('sin', '4')
            self._sinCount += 1
            self._opSituation.append('s')
        elif isinstance(op4, list):
            self._op4 = self._SinOrFM('fm', '4', op4[0], op4[1])
            self._fmCount += 1
            self._opSituation.append('f')

        self._countChecker()

        if isinstance(op5, str):
            self._op5 = self._SinOrFM('sin', '5')
            self._sinCount += 1
            self._opSituation.append('s')
        elif isinstance(op5, list):
            self._op5 = self._SinOrFM('fm', '5', op5[0], op5[1])
            self._fmCount += 1
            self._opSituation.append('f')

        self._countChecker()

        if isinstance(op6, str):
            self._op6 = self._SinOrFM('sin', '6')
            self._sinCount += 1
            self._opSituation.append('s')
        elif isinstance(op6, list):
            self._op6 = self._SinOrFM('fm', '6', op6[0], op6[1])
            self._fmCount += 1
            self._opSituation.append('f')

        self._countChecker()

    def _detuneGenerator(self, det1 = None, det2 = None, det3 = None, det4 = None, det5 = None, det6 = None):
        if det1 != None:
            self._detune1 = Sig(det1)
            self._ctrlDet1 = det1

        if det2 != None:
            self._detune2 = Sig(det2)
            self._ctrlDet2 = det2

        if det3 != None:
            self._detune3 = Sig(det3)
            self._ctrlDet3 = det3

        if det4 != None:
            self._detune4 = Sig(det4)
            self._ctrlDet4 = det4

        if det5 != None:
            self._detune5 = Sig(det5)
            self._ctrlDet5 = det5

        if det6 != None:
            self._detune6 = Sig(det6)
            self._ctrlDet6 = det6

    def _ctrlGenerator(self, op1=None, op2=None, op3=None, op4=None, op5=None, op6=None):
        """
        This method must have the exact same input as operatorGenerator().
        """
        if self._opSituation[0] == 'f':
            ratiomap1 = SLMap(1, 64, 'lin', 'ratio', op1[0], 'int')
            indexmap1 = SLMap(0, 0.5, 'lin', 'index', op1[1])
            self._op1.ctrl(map_list=[ratiomap1, indexmap1], title='Operator 1')
        if self._opSituation[0] != None:
            self._detune1.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', self._ctrlDet1, 'int')], title='detune OP 1')

        if self._opSituation[1] == 'f':
            ratiomap2 = SLMap(1, 64, 'lin', 'ratio', op2[0], 'int')
            indexmap2 = SLMap(0, 0.5, 'lin', 'index', op2[1])
            self._op2.ctrl(map_list=[ratiomap2, indexmap2], title='Operator 2')
        if self._opSituation[1] != None:
            self._detune2.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', self._ctrlDet2, 'int')], title='detune OP 2')

        if self._opSituation[2] == 'f':
            ratiomap3 = SLMap(1, 64, 'lin', 'ratio', op3[0], 'int')
            indexmap3 = SLMap(0, 0.5, 'lin', 'index', op3[1])
            self._op3.ctrl(map_list=[ratiomap3, indexmap3], title='Operator 3')
        if self._opSituation[2] != None:
            self._detune3.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', self._ctrlDet3, 'int')], title='detune OP 3')

        if len(self._opSituation) == 3:
            return

        if self._opSituation[3] == 'f':
            ratiomap4 = SLMap(1, 64, 'lin', 'ratio', op4[0], 'int')
            indexmap4 = SLMap(0, 0.5, 'lin', 'index', op4[1])
            self._op4.ctrl(map_list=[ratiomap4, indexmap4], title='Operator 4')
        if self._opSituation[3] != None:
            self._detune4.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', self._ctrlDet4, 'int')], title='detune OP 4')

        if len(self._opSituation) == 4:
            return

        if self._opSituation[4] == 'f':
            ratiomap5 = SLMap(1, 64, 'lin', 'ratio', op5[0], 'int')
            indexmap5 = SLMap(0, 0.5, 'lin', 'index', op5[1])
            self._op5.ctrl(map_list=[ratiomap5, indexmap5], title='Operator 5')
        if self._opSituation[4] != None:
            self._detune5.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', self._ctrlDet5, 'int')], title='detune OP 5')

        if len(self._opSituation) == 5:
            return

        if self._opSituation[5] == 'f':
            ratiomap6 = SLMap(1, 64, 'lin', 'ratio', op6[0], 'int')
            indexmap6 = SLMap(0, 0.5, 'lin', 'index', op6[1])
            self._op6.ctrl(map_list=[ratiomap6, indexmap6], title='Operator 6')
        if self._opSituation[5] != None:
            self._detune6.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', self._ctrlDet6, 'int')], title='detune OP 6')

    def _outputGenerator(self):
        op_values = [getattr(self, f"_op{i}", 0) for i in range(1, 7)]
        self._output = sum(op_values[:self._fmCount + self._sinCount])


    def _countChecker(self):
        count = self._sinCount + (2*self._fmCount)
        if count > 6:
            raise OperatorNumberError(
                "The must be less than 7, otherwise it wouldn't be a dx7")

    def _SinOrFM(self, obj, number, ratio=None, index=None):
        detune_value = getattr(self, f'_detune{number}')
        frequency = self._freqs * (2 ** (detune_value / 1200))

        if obj == 'fm':
            return FM(frequency, ratio, index, mul=self._amps)
        else:
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
        self._getLayout('./Images/algoTwentynine.png')
        self._detuneGenerator(0, 0, 0, 0)
        self._operatorGenerator([1, 0], [1, 0], 'sin', 'sin')
        self._outputGenerator()

    def _6(self):
        self._getLayout('./Images/algoSix.png')
        self._detuneGenerator(0, 0, 0)
        self._operatorGenerator([1, 0], [1, 0], [1, 0])
        self._outputGenerator()

    def _bell(self):
        self._getLayout('./Images/algoTwentynine.png')
        self._detuneGenerator(2, 6, -13, -7)
        self._operatorGenerator([13, 0.371], [31, 0.188], 'sin', 'sin')
        self._outputGenerator()

    def _electricpiano(self):
        self._getLayout('./Images/algoSix.png')
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
