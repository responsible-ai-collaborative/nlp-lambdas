# Source: https://www.quora.com/In-Python-how-can-I-skip-an-iteration-in-a-for-loop-if-it-takes-longer-than-5-secs

from threading import Timer 
class LoopStopper: 
    def __init__(self, seconds): 
        self._loop_stop = False 
        self._seconds = seconds 
  
    def _stop_loop(self): 
        self._loop_stop = True
    
    def run(self, generator_expression, task): 
        """ Execute a task a number of times based on the generator_expression""" 
        t = Timer(self._seconds, self._stop_loop) 
        t.start() 
        for i in generator_expression: 
            task(i) 
            if self._loop_stop: 
                break 
        t.cancel() # Cancel the timer if the loop ends ok. \

    def runExcept(self, generator_expression, task, exceptionOnFail): 
        """ Execute a task a number of times based on the generator_expression""" 
        t = Timer(self._seconds, self._stop_loop) 
        t.start() 
        
        keep_going = True
        while keep_going:
            print('\nwow')
            line = next(generator_expression, None)
            print(line)
            if line is not None:
                res = task(line)
                if res == 0: keep_going = False
            elif self._loop_stop: raise exceptionOnFail

        # for i in generator_expression:
        #     res = task(i)
        #     if res == 0: break
        #     if self._loop_stop: raise exceptionOnFail

        t.cancel() # Cancel the timer if the loop ends ok. 