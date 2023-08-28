from pyo import *
import math

class Distortion(PyoObject):
    """
    Exponential distortion

    Apply a kind of exponential function.

    :Parent: :py:class:`PyoObject`

    :Args:

        input: PyoObject
            Input signal to process.
        gain: int or float, optional
            Amount of distortion applied to the signal.
            Defaults to 7.0.

    >>> s = Server().boot()
    >>> s.start()
    >>> signal = SfPlayer(MY_PATH, loop=True)
    >>> d = Distortion(signal, gain=7.0, mul=1, add=0).out() 
    
    """  
    def __init__(self, input, gain=7.0, mul=1, add=0):
        super().__init__(mul, add)
        self.checktype(gain)

        self._input = input
        self._gain = gain
        self._output = self._apply_table()
        self._base_objs = self._output.getBaseObjects()
    
    def _f(self,x):
        return math.copysign(1,x) * (1 - math.exp(-abs(x*self._gain)))
    
    def _create_table(self): 
        tablesize = 8192
        xvals = [i*2*self._gain/tablesize -self._gain for i in range(tablesize)]
        fvals = [self._f(x) for x in xvals]
        table = DataTable(size=tablesize, init=fvals)
        table.view()
        return table
 
    def _apply_table(self):
        self._output = Lookup(self._create_table(),self._input)
        self._output = Interp(self._input, self._output, interp=0.5)
        self._output.ctrl()
        return self._output
 
    def play(self, dur=0, delay=0):
        self._output.play(dur,delay)
        return self
    
    def stop(self, wait=0):
        self._output.stop(wait)
        return self
    
    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output = Pan(self._output)
        self._output.out(chnl,inc,dur,delay)
        return self
    
    def __repr__(self):
        return super().__repr__()
    
    @staticmethod
    def checktype(value):
        if not isinstance (value, (int,float)):
            raise TypeError("Gain must be numeric")
    
class Overdrive(PyoObject):
    """
    Overdrive distortion, based on symmetrical soft clipping

    Apply a kind of symmetrical soft clipping function.

    :Parent: :py:class:`PyoObject`

    :Args:

        input: PyoObject
            Input signal to process.
        threshold: int or float, optional
            Value beyond which the input signal begins to be distorted.
            Defaults to 1/3, typical threshold for symmetrical soft clipping

    >>> s = Server().boot()
    >>> s.start()
    >>> signal = SfPlayer(MY_PATH, loop=True)
    >>> d = Overdrive(signal, threshold=1/3, mul=1, add=0).out() 
    
    """
    def __init__(self, input, threshold=1/3, mul=1, add=0):
        super().__init__(mul,add)
        self.checktype(threshold)

        self._input = input
        self._threshold = threshold
        self._output = self._apply_table()
        self._base_objs = self._output.getBaseObjects() 

    def _f(self, x):
        sgnx = math.copysign(1,x)
        if abs(x) <= self._threshold: 
            y = 2*x
        elif abs(x) <= 2 * self._threshold:
            y = sgnx * ((3 - (2 - 3 * abs(x)) ** 2) / 3)
        else:
            y = sgnx
        return y
        
    def _create_table(self): 
        tablesize = 8192 
        xvals = [i*2/tablesize - 1 for i in range(tablesize)]
        fvals = [self._f(x) for x in xvals]
        table = DataTable(size=tablesize, init=fvals)
        table.view()
        return table
 
    def _apply_table(self):
        self._output = Lookup(self._create_table(),self._input)
        self._output = Interp(self._input, self._output, interp=0.5)
        self._output.ctrl()
        return self._output
    
    def play(self, dur=0, delay=0):
        self._output.play(dur,delay)
        return self
    
    def stop(self, wait=0):
        self._output.stop(wait)
        return self
    
    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output = Pan(self._output)
        self._output.out(chnl,inc,dur,delay)
        return self
    
    def __repr__(self):
        return super().__repr__()
    
    @staticmethod
    def checktype(value):
        if not isinstance (value, (int,float)):
            raise TypeError("Threshold must be numeric")
    
class Fuzz(PyoObject):
    """
    Fuzz distortion, creates a warm and gritty tone similar to a nasal sound

    Apply a type of distortion effect that intentionally adds harmonic content and clipping to a sound signal. 
    

    :Parent: :py:class:`PyoObject`

    :Args:

        input: PyoObject
            Input signal to process.
        gain: int or float, optional
            Amount of distortion applied to the signal.
            Defaults to 7.0.
        threshold: int or float, optional
            Value beyond which the input signal begins to be distorted.
            Defaults to 0.5.

    >>> s = Server().boot()
    >>> s.start()
    >>> signal = SfPlayer(MY_PATH, loop=True)
    >>> d = Fuzz(signal, gain = 7.0, threshold=0.5, mul=1, add=0).out() 
    
    """
    def __init__(self, input, gain=7.0, threshold=0.5, mul=1, add=0):
        super().__init__(mul, add)
        values = [gain, threshold]
        for val in values:
            self.checktype(val)

        self._input = input
        self._gain = gain
        self._threshold = threshold
        self._output = self._apply_table()
        self._base_objs = self._output.getBaseObjects() 
    
    def _f(self, x):
        return math.copysign(1,x) * (1 - math.exp(-abs(self._gain * x))) / (1 - math.exp(-abs(self._gain)))

    def _create_table(self): 
        tablesize = 8192
        xvals = [i*2*self._gain/tablesize -self._gain for i in range(tablesize)]
        fvals = [self._f(x) for x in xvals]
        table = DataTable(size=tablesize, init=fvals)
        table.view()
        return table
 
    def _apply_table(self):
        self._output = Lookup(self._create_table(),self._input)
        self._output = Interp(self._input, self._output, interp=0.5)
        self._output.ctrl()
        return self._output
    
    def play(self, dur=0, delay=0):
        self._output.play(dur,delay)
        return self
    
    def stop(self, wait=0):
        self._output.stop(wait)
        return self
    
    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output = Pan(self._output)
        self._output.out(chnl,inc,dur,delay)
        return self
    
    def __repr__(self):
        return super().__repr__()
    
    @staticmethod
    def checktype(value):
        if not isinstance (value, (int,float)):
            raise TypeError("Gain and threshold must be numeric")
    
class Tube(PyoObject):
    """
    Tube distortion, often associated with vintage equipment 

    It's a type of audio distortion that occurs when an audio signal is amplified using vacuum tubes;     
    it starts to clip and distort in a warm and harmonically rich manner. 
    Then the sound passes from high-pass and a low-pass filter.
    

    :Parent: :py:class:`PyoObject`

    :Args:

        input: PyoObject
            Input signal to process.
        dist: int or float, optional
            Distortion's character, higher number=higher distortion.
            Defaults to 8.0.
        Q: int or float, optional
            Controls the linearity of the transfer function for low input levels, more negative=more linear.
            Defaults to -0.2.
        rh: int or float, optional
            Placement of poles in the HP filter which removes the DC component.
            Defaults to 0.95.
        rl: int or float, optional
            The pole placement in the LP filter used to simulate capacitances in a tube amplifier.
            Defaults to 0.95.

    >>> s = Server().boot()
    >>> s.start()
    >>> signal = SfPlayer(MY_PATH, loop=True)
    >>> d = Tube(signal, dist=8.0, Q=-0.2, rh=0.95, rl=0.95, mul=1, add=0).out() 
    
    """
    def __init__(self, input, dist=8.0, Q=-0.2, rh=0.95, rl=0.95, mul=1, add=0):
        super().__init__(mul,add)
        values = [dist, Q, rh, rl]
        for val in values:
            self.checktype(val)

        self._input = input
        self._dist = dist 
        self._Q = Q 
        self._rh = rh 
        self._rl = rl 
        self._output = self._apply_table()
        self._base_objs = self._output.getBaseObjects()

    def _f(self, x):
        if x != self._Q or self._Q != 0: 
            y = ((x - self._Q)/(1 - (math.exp(-self._dist * (x - self._Q))))) + (self._Q/(1 - (math.exp(self._dist * self._Q))))
        else: 
            y = (1/self._dist) + (self._Q/(1 - (math.exp(self._dist * self._Q))))
        return y
    
    def _create_table(self): 
        tablesize = 8192 
        xvals = [i*2/tablesize - 1 for i in range(tablesize)]
        fvals = [self._f(x) for x in xvals]
        table = DataTable(size=tablesize, init=fvals)
        table.view()
        return table
 
    def _apply_table(self):
        self._output = Lookup(self._create_table(),self._input)
        self._output = Interp(self._input, self._output, interp=0.5)
        self._output.ctrl()
        return self._output
    
    def _apply_biquad(self, input_signal, a_coeffs, b_coeffs):
        # a and b are the coefficients of the numerator and denominator polynomials in the transfer function of the filter
        # the numerator polynomial is multiplied by the input signal, the denominator one is multiplied by the delayed output values
        outputs = [Sig(0) for _ in range(len(b_coeffs))]
        delays = [Delay(input_signal) for _ in range(len(b_coeffs))]
        
        for i in range(len(b_coeffs)):
            outputs[i] = delays[i] * b_coeffs[i]
        
        for i in range(1, len(a_coeffs)):
            for j in range(i):
                outputs[i] -= delays[j] * a_coeffs[i - j]
        
        output_sum = sum(outputs)
        
        return output_sum
    
    def play(self, dur=0, delay=0):
        self._output.play(dur,delay)
        return self
    
    def stop(self, wait=0):
        self._output.stop(wait)
        return self
    
    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output = Pan(self._output)
        self._output.out(chnl,inc,dur,delay)
        return self
    
    def __repr__(self):
        return super().__repr__()
    
    @staticmethod
    def checktype(value):
        if not isinstance (value, (int,float)):
            raise TypeError("Dist, Q, rh, rl must be numeric")
    
class Bitcrush(PyoObject):
    """
    Bitcrush distortion, emulates the artifacts that occur when digital audio is heavily compressed or processed at lower quality

    Audio effect that intentionally reduces the bit depth and sample rate of a digital audio signal, leading to a lo-fi, "crushed" sound.
    

    :Parent: :py:class:`PyoObject`

    :Args:

        input: PyoObject
            Input signal to process.
        gain: int or float, optional
            Amount of distortion applied to the signal.
            Defaults to 7.0.
        bitDepth: int or float, optional
            Refers to the number of bits used to represent the amplitude of a sample in a sound waveform.
            Defaults to 4.0.

    >>> s = Server().boot()
    >>> s.start()
    >>> signal = SfPlayer(MY_PATH, loop=True)
    >>> d = Bitcrush(signal, gain = 7.0, bitDepth=4.0, mul=1, add=0).out() 
    
    """
    def __init__(self, input, gain=7.0, bitDepth=4.0, mul=1, add=0):
        super().__init__(mul,add)
        values = [gain, bitDepth]
        for val in values:
            self.checktype(val)

        self._input = input
        self._gain = gain
        self._bitDepth = bitDepth 
        self._output = self._apply_bitcrush()
        self._base_objs = self._output.getBaseObjects() 

    def _apply_bitcrush(self):
        self._output = Degrade(self._input, self._bitDepth)
        self._output = Interp(self._input, self._output, interp=0.5)
        self._output.ctrl()
        return self._output
    
    def play(self, dur=0, delay=0):
        self._output.play(dur,delay)
        return self
    
    def stop(self, wait=0):
        self._output.stop(wait)
        return self
    
    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output = Pan(self._output)
        self._output.out(chnl,inc,dur,delay)
        return self
    
    def __repr__(self):
        return super().__repr__()
    
    @staticmethod
    def checktype(value):
        if not isinstance (value, (int,float)):
            raise TypeError("This value must be numeric")
    
class Zap(PyoObject):
    """
    Zap distortion

    It's a type of audio distortion based on a sin function.

    :Parent: :py:class:`PyoObject`

    :Args:

        input: PyoObject
            Input signal to process.
        gain: int or float, optional
            Amount of distortion applied to the signal.
            Defaults to 7.0.

    >>> s = Server().boot()
    >>> s.start()
    >>> signal = SfPlayer(MY_PATH, loop=True)
    >>> d = Zap(signal, gain=7.0, mul=1, add=0).out() 
    
    """
    def __init__(self, input, gain=7.0, mul=1, add=0):
        super().__init__(mul, add)
        self.checktype(gain)

        self._input = input
        self._gain = gain
        self._output = self._apply_table()
        self._base_objs = self._output.getBaseObjects() 
    
    def _f(self, x):
        y = math.sin(3*x)
        return y

    def _create_table(self): 
        tablesize = 8192 
        xvals = [i*2*self._gain/tablesize -self._gain for i in range(tablesize)]
        fvals = [self._f(x) for x in xvals]
        table = DataTable(size=tablesize, init=fvals)
        table.view()
        return table
 
    def _apply_table(self):
        self._output = Lookup(self._create_table(),self._input)
        self._output = Interp(self._input, self._output, interp=0.5)
        self._output.ctrl()
        return self._output
    
    def play(self, dur=0, delay=0):
        self._output.play(dur,delay)
        return self
    
    def stop(self, wait=0):
        self._output.stop(wait)
        return self
    
    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output = Pan(self._output)
        self._output.out(chnl,inc,dur,delay)
        return self
    
    def __repr__(self):
        return super().__repr__()
    
    @staticmethod
    def checktype(value):
        if not isinstance (value, (int,float)):
            raise TypeError("This value must be numeric")
    
class Crunch(PyoObject):
    """
    Crunch distortion creates a harmonically rich and textured sound

    It's an audio effect that produces a gritty and saturated sound by adding moderate levels of clipping and distortion to an audio signal.
    Crunch distortion aims to provide a balance between clean and distorted tones. 
    
    :Parent: :py:class:`PyoObject`

    :Args:

        input: PyoObject
            Input signal to process.
        threshold: int or float, optional
            Value beyond which the input signal begins to be distorted.
            Defaults to 1/3.

    >>> s = Server().boot()
    >>> s.start()
    >>> signal = SfPlayer(MY_PATH, loop=True)
    >>> d = Crunch(signal, threshold=1/3, mul=1, add=0).out() 
    
    """
    def __init__(self, input, threshold=1/3, mul=1, add=0):
        super().__init__(mul, add)
        self.checktype(threshold)

        self._input = input
        self._threshold = threshold
        self._output = self._apply_table()
        self._base_objs = self._output.getBaseObjects() 
    
    def _f(self, x):
        sgnx = math.copysign(1,x)
        if abs(x) <= 3/2 * self._threshold + 1/15: 
            y = sgnx * ((4 - (2 - 3 * abs(x)) ** 2) / 5)
        elif abs(x) <= 2 * self._threshold:
            y = sgnx * ((4 - (3 - 3 * abs(x)) ** 2) / 3)
        else:
            y = sgnx
        return y

    def _create_table(self): 
        tablesize = 8192
        xvals = [i*2/tablesize -1 for i in range(tablesize)]
        fvals = [self._f(x) for x in xvals]
        table = DataTable(size=tablesize, init=fvals)
        table.view()
        return table
 
    def _apply_table(self):
        self._output = Lookup(self._create_table(),self._input)
        self._output = Interp(self._input, self._output, interp=0.5)
        self._output.ctrl()
        return self._output
    
    def play(self, dur=0, delay=0):
        self._output.play(dur,delay)
        return self
    
    def stop(self, wait=0):
        self._output.stop(wait)
        return self
    
    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output = Pan(self._output)
        self._output.out(chnl,inc,dur,delay)
        return self
    
    def __repr__(self):
        return super().__repr__()
    
    @staticmethod
    def checktype(value):
        if not isinstance (value, (int,float)):
            raise TypeError("Gain and threshold must be numeric")
        
if __name__ == "__main__": 

    s = Server(buffersize=1024)               
    s.setAmp(0.1)
    s.boot()

    # chose which output you want to test
    file = r"C:\Users\Sofia\Desktop\ProjectAvanzini\effects\nylon_guitar_loop_B1.wav" 
    input = SfPlayer(file, speed=1, loop=True, mul=0.4)
    #input = Sine(440)

    """output = Distortion(input, 10)
    output.out()
    Spectrum([input,output])

    output = Overdrive(input)
    output.out()
    Spectrum([input,output])

    output = Fuzz(input, 40)
    output.out()
    Spectrum([input,output])

    output = Tube(input, 100)
    output.out()
    Spectrum([input,output])"""

    output = Bitcrush(input, 40)
    output.out()
    Spectrum([input,output])

    """output = Zap(input, 40)
    output.out()
    Spectrum([input,output])

    output = Crunch(input)
    output.out()
    Spectrum([input,output])"""

    s.gui(locals())