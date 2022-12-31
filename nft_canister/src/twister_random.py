# type: ignore

# Period parameters
N = 624
M = 397
MATRIX_A = 0x9908b0df   # constant vector a
UPPER = 0x80000000  # most significant w-r bits
LOWER = 0x7fffffff  # least significant r bits

class MersenneTwister:
    def __init__(self, s=None):
        self.mt = [0]*N  # the array for the state vector
        self.mti = N+1   # mti==N+1 means mt is not initialized
        self.gauss_next = 0.0
        self.gauss_switch = 0
        self.seed(s)

    def seed(self, s=None):
        # if not s: s = long(time.time() * 256)
        if not s: s = 0
        #self.init_genrand(long(s))
        self.init_by_array([s])

    def random(self):
        return self.genrand_res53()

    def getstate(self):
        """Return internal state; can be passed to setstate() later."""
        return self.mti, self.mt, self.gauss_next, self.gauss_switch

    def setstate(self, state):
        """Restore internal state from object returned by getstate()."""
        self.mti, self.mt, self.gauss_next, self.gauss_switch = state

    def jumpahead(self, n):
        """(Not implemented - Does nothing)
        Provided for basic compatibility with CPython's random modules."""
        pass

## -------------------- pickle support  -------------------

    def __getstate__(self): # for pickle
        return self.getstate()

    def __setstate__(self, state):  # for pickle
        self.setstate(state)

    def __reduce__(self):
        return self.__class__, (), self.getstate()

    """
    =======================================================================
    Mersenne Twister code
    The following methods closely match the original C source code.
    =======================================================================
    """

    # initializes mt with a seed
    def init_genrand(self, s):
        self.mt[0]= s & 0xffffffff
        for self.mti in range(1,N):
            self.mt[self.mti] = (1812433253 * (self.mt[self.mti-1] ^ \
                    ((self.mt[self.mti-1] >> 30) & 3)) + self.mti)

            self.mt[self.mti] &= 0xffffffff
            # for >32 bit machines
        self.mti += 1

    # initialize by an array with array-length
    # init_key is the array for initializing keys
    # slight change for C++, 2004/2/26
    def init_by_array(self, init_key, key_length=-1):
        if key_length < 0:
            key_length = len(init_key)
            self.init_genrand(19650218)
            i,j = 1,0
            k = max(N, key_length)
            for k in range(k,0,-1):
                self.mt[i] = (self.mt[i] ^ ((self.mt[i-1] ^ ((self.mt[i-1]>>30)&3))\
                        * 1664525)) + init_key[j] + j  # non linear
                self.mt[i] &= 0xffffffff  # for WORDSIZE > 32 machines
                i+=1; j+=1
                if (i>=N): self.mt[0] = self.mt[N-1]; i=1
                if (j>=key_length): j=0

            for k in range(N-1, 0, -1):
                self.mt[i] = (self.mt[i] ^ ((self.mt[i-1] ^ ((self.mt[i-1]>>30)&3))\
                        * 1566083941)) - i   # non linear
                self.mt[i] &= 0xffffffff  # for WORDSIZE > 32 machines
                i+=1
                if (i>=N): self.mt[0] = self.mt[N-1]; i=1

            self.mt[0] = 0x80000000  # MSB is 1; assuring non-zero initial array


    # generates a random number on [0,0xffffffff]-interval
    def genrand_int32(self):
        mag01 = [0x0, MATRIX_A]
        # mag01[x] = x * MATRIX_A  for x=0,1

        if (self.mti >= N):  # generate N words at one time

            if (self.mti == N+1):  # if init_genrand() has not been called,
                self.init_genrand(5489)  # a default initial seed is used

            for kk in range(N-M):
                y = (self.mt[kk] & UPPER) | (self.mt[kk+1] & LOWER)
                self.mt[kk]= self.mt[kk+M] ^ ((y>>1)&LOWER) ^ mag01[y&0x1]
                    # JM: Added "& LOWER" to (y>>1) for int repr of uint
            
            for kk in range(kk+1, N-1):  # k+1 because range omits last value
                y = (self.mt[kk] & UPPER) | (self.mt[kk+1] & LOWER)
                self.mt[kk] = self.mt[kk+(M-N)] ^ ((y>>1)&LOWER) ^ mag01[y&0x1]
            
            y = (self.mt[N-1] & UPPER) | (self.mt[0] & LOWER)
            self.mt[N-1] = self.mt[M-1] ^ ((y>>1) & LOWER) ^ mag01[y&0x1]
            self.mti = 0

        y = self.mt[self.mti]
        self.mti += 1

        # Tempering
        # (JM: Added "& ~(-1 << (32-B))" for signed int repr of unsigned int)
        y ^= (y >> 11) & ~(-1 << (32-11))
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= (y >> 18) & ~(-1 << (32-18))

        return y


    # generates a random number on [0,1]-real-interval
    def genrand_real1(self):
        #return self.genrand_int32()*(1.0/4294967295.0)
        # divided by 2^32-1
        r = self.genrand_int32()*(1.0/4294967295.0)
        return r + (r<0)  # (JM: Added so that int or unsigned int can be used)

    # generates a random number on [0,1)-real-interval
    def genrand_real2(self):
        #return self.genrand_int32()*(1.0/4294967296.0)
        # divided by 2^32
        r = self.genrand_int32()*(1.0/4294967296.0)
        return r + (r<0)  # (JM: Added so that int or unsigned int can be used)

    # generates a random number on (0,1)-real-interval
    def genrand_real3(self):
        #return (float(self.genrand_int32()) + 0.5)*(1.0/4294967296.0)
        r = float(self.genrand_int32())
        return (r + (r>0)-0.5)*(1.0/4294967296.0) + (r<0)
        # divided by 2^32

    # generates a random number on [0,1) with 53-bit resolution
    def genrand_res53(self):
        a = (self.genrand_int32()>>5) & ~(-1 << (32-5))
        b = (self.genrand_int32()>>6) & ~(-1 << (32-6))
        return (a*67108864.0+b)*(1.0/9007199254740992.0); 

    # These real versions are due to Isaku Wada, 2002/01/09 added



    """
    =======================================================================
    CPython code
    The following methods are taken from random.py
    =======================================================================
    """


## -------------------- integer methods  -------------------

    def randrange(self, start, stop, step=1):
        """Choose a random item from range(start, stop[, step]).
        This fixes the problem with randint() which includes the
        endpoint; in Python this is usually not what you want.
        Do not supply the 'int', 'default', and 'maxwidth' arguments.
        """
        # Note: In CPython, stop is optional, with a default of None. However,
        # this behavior doesn't seem possible in Shed Skin unless scalar
        # variables can have a None value.

        istart = int(start)
        if istart != start:
            raise(ValueError, "non-integer arg 1 for randrange()")

        istop = int(stop)
        if istop != stop:
            raise(ValueError, "non-integer stop for randrange()")
        width = istop - istart
        if step == 1 and width > 0:
            return int(istart + int(self.random()*width))
        if step == 1:
            raise(ValueError, "empty range for randrange()")

        # Non-unit step argument supplied.
        istep = int(step)
        if istep != step:
            raise(ValueError, "non-integer step for randrange()")
        if istep > 0:
            n = (width + istep - 1) / istep
        elif istep < 0:
            n = (width + istep + 1) / istep
        else:
            raise(ValueError, "zero step for randrange()")

        if n <= 0:
            raise(ValueError, "empty range for randrange()")

        return istart + istep*int(self.random() * n)


    def randint(self, a, b):
        """Return random integer in range [a, b], including both end points.
        """
        return self.randrange(a, b+1)


## -------------------- sequence methods  -------------------

    def choice(self, seq):
        """Choose a random element from a non-empty sequence."""
        return seq[int(self.random() * len(seq))]

    def shuffle(self, x):
        """x, random=random.random -> shuffle list x in place; return None.
        Note that for even rather small len(x), the total number of
        permutations of x is larger than the period of most random number
        generators; this implies that "most" permutations of a long
        sequence can never be generated.
        """
        # Note: CPython supports another optional arg, a function that is
        # called instead of random.

        for i in range(len(x)-1, 0, -1):
            # pick an element in x[:i+1] with which to exchange x[i]
            j = int(self.random() * (i+1))
            x[i], x[j] = x[j], x[i]