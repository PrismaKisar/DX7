from pyo import *
from PIL import Image

class ImplementationError(Exception): pass

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

    def __init__(self, mode = '6'):
        if not isinstance(mode, str):
            raise TypeError('mode must be string')
        self._mode = mode
        PyoObject.__init__(self, 1, 0)
        notes = Notein(scale=1, poly=32)
        notes.keyboard()
        self._freqs = notes["pitch"]
        self._amps = Port(notes["velocity"], risetime=0.005, falltime=0.2)
        self._amps.ctrl()

        if mode == '6':
            self._algoSix()
        elif mode == '29':
            self._algoTwentynine()
        elif mode == 'electric piano':
            self._electricPiano()
        elif mode == 'bell':
            self._bell()
        else: raise ImplementationError(f'Mode {mode} has not yet been implemented')

        self._base_objs = self._output.getBaseObjects()

    def _algoSix(self):
        self._getLayout('./Images/algoSix.png')

        # --- Detune ---
        detune1 = Sig(1)
        detune1.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 0, 'int')], title='detune OP 1')
        detune2 = Sig(1)
        detune2.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 0, 'int')], title='detune OP 3')
        detune3 = Sig(1)
        detune3.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 0, 'int')], title='detune OP 5')

        # --- Operators Generator ---
        tones1 = FM(self._freqs*(2**(detune1/1200)), mul=self._amps)
        tones2 = FM(self._freqs*(2**(detune2/1200)), mul=self._amps)
        tones3 = FM(self._freqs*(2**(detune3/1200)), mul=self._amps)

        # --- Map ---
        ratiomap1 = SLMap(1,64,'lin','ratio',1,'int')
        ratiomap2 = SLMap(1,64,'lin','ratio',1,'int')
        ratiomap3 = SLMap(1,64,'lin','ratio',1,'int')
        indexmap1 = SLMap(0,0.5,'lin','index',0)
        indexmap2 = SLMap(0,0.5,'lin','index',0)
        indexmap3 = SLMap(0,0.5,'lin','index',0)

        # --- Operator ---
        tones1.ctrl(map_list=[ratiomap1, indexmap1], title='1')
        tones2.ctrl(map_list=[ratiomap2, indexmap2], title='3')
        tones3.ctrl(map_list=[ratiomap3, indexmap3], title='5')
        self._output = tones1 + tones2 + tones3
   
    def _algoTwentynine(self):
        self._getLayout('./Images/algoTwentynine.png')

        # --- Detune ---
        detune1 = Sig(1)
        detune1.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 0, 'int')], title='detune OP 1')
        detune2 = Sig(1)
        detune2.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 0, 'int')], title='detune OP 2')
        detune3 = Sig(1)
        detune3.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 0, 'int')], title='detune OP 3')
        detune4 = Sig(1)
        detune4.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 0, 'int')], title='detune OP 5')

        # --- Operators Generator ---
        tones1 = FM(self._freqs*(2**(detune1/1200)), mul=self._amps)
        tones2 = FM(self._freqs*(2**(detune2/1200)), mul=self._amps)
        tones3 = Sin(self._freqs*(2**(detune3/1200)), mul=self._amps)
        tones4 = Sin(self._freqs*(2**(detune4/1200)), mul=self._amps)

        # --- Map ---
        ratiomap1 = SLMap(1,64,'lin','ratio',1,'int')
        ratiomap2 = SLMap(1,64,'lin','ratio',1,'int')
        indexmap1 = SLMap(0,0.5,'lin','index',0)
        indexmap2 = SLMap(0,0.5,'lin','index',0)

        # --- Operator ---
        tones1.ctrl(map_list=[ratiomap1, indexmap1], title='3')
        tones2.ctrl(map_list=[ratiomap2, indexmap2], title='5')
        self._output = tones1 + tones2 + tones3 + tones4

    def _bell(self):
        self._getLayout('./Images/algoTwentynine.png')

        # --- Detune ---
        self._detune1 = Sig(2)
        self._detune2 = Sig(6)
        self._detune3 = Sig(-13)
        self._detune4 = Sig(-7)

        # --- Operators Generator ---
        self._tones1 = FM(self._freqs*(2**(self._detune1/1200)), 13, 0.371, mul=self._amps)
        self._tones2 = FM(self._freqs*(2**(self._detune2/1200)), 31, 0.188, mul=self._amps)
        self._tones3 = Sin(self._freqs*(2**(self._detune3/1200)), mul=self._amps)
        self._tones4 = Sin(self._freqs*(2**(self._detune4/1200)), mul=self._amps)

        self._output = self._tones1 + self._tones2 + self._tones3 + self._tones4

    def _electricPiano(self):
        self._getLayout('./Images/algoSix.png')

        # --- Detune ---
        self._detune1 = Sig(-3)
        self._detune2 = Sig(0)
        self._detune3 = Sig(7)

        # --- Operators Generator ---
        self._tones1 = FM(self._freqs*(2**(self._detune1/1200)), 1, 0.060, self._amps)
        self._tones2 = FM(self._freqs*(2**(self._detune2/1200)), 14, 0.004, self._amps)
        self._tones3 = FM(self._freqs*(2**(self._detune3/1200)), 1, 0.023, self._amps)

        self._output = self._tones1 + self._tones2 + self._tones3

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
        self._output = Freeverb(self._output,0,0,0)
        self._output.ctrl(title='Reverb')
        self._output.out(chnl, inc, dur, delay)
        return self

    def ctrl(self):
        if self._mode == 'electric piano':
            self._detune1.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', -3, 'int')], title='detune OP 1')
            self._detune2.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 0, 'int')], title='detune OP 3')
            self._detune3.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 7, 'int')], title='detune OP 5')

            # --- Map ---
            ratiomap1 = SLMap(0.5,64,'lin','ratio',1,'int')
            ratiomap2 = SLMap(1,64,'lin','ratio',14,'int')
            ratiomap3 = SLMap(1,64,'lin','ratio',1,'int')
            indexmap1 = SLMap(0,0.5,'lin','index',0.060)
            indexmap2 = SLMap(0,0.5,'lin','index',0.004)
            indexmap3 = SLMap(0,0.5,'lin','index',0.023)

            # --- Operator ---
            self._tones1.ctrl(map_list=[ratiomap1, indexmap1], title='1')
            self._tones2.ctrl(map_list=[ratiomap2, indexmap2], title='3')
            self._tones3.ctrl(map_list=[ratiomap3, indexmap3], title='5')

        elif self._mode == 'bell':
            self._detune1.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 2, 'int')], title='detune OP 1')
            self._detune2.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', 6, 'int')], title='detune OP 2')
            self._detune3.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', -13, 'int')], title='detune OP 3')
            self._detune4.ctrl(map_list=[SLMap(-15, 15, 'lin', 'value', -7, 'int')], title='detune OP 5')
            
            # --- Map ---
            ratiomap1 = SLMap(1,64,'lin','ratio',13,'int')
            ratiomap2 = SLMap(1,64,'lin','ratio',31,'int')
            indexmap1 = SLMap(0,0.5,'lin','index',0.371)
            indexmap2 = SLMap(0,0.5,'lin','index',0.188)

            # --- Operator ---
            self._tones1.ctrl(map_list=[ratiomap1, indexmap1], title='3')
            self._tones2.ctrl(map_list=[ratiomap2, indexmap2], title='5')
                    
    def __repr__(self):
        return super().__repr__()

if __name__ == '__main__':
    s = Server().boot()
    s.setAmp(0.1)
    
    a = DX7('bell').out()
    a.ctrl()

    Spectrum(a)

    s.gui(locals())




   



   
        

    
