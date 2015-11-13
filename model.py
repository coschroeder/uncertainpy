### TODO
# Check if cvode is active, if it is inactive avoid doing the interpolation
# Currently no way of testing if cvode is active. One way is to test if the amount of
# numbers between two different simulations are different

# Move parameter and parameter_string to uncertainty

import os
import subprocess
#import time
import sys
import glob

import numpy as np
import multiprocess as mp

from xvfbwrapper import Xvfb



class Model():
    def __init__(self, modelfile, modelpath, parameterfile, parameters,
                 memory_threshold=None, supress_output=False):
        """
        modelfile: Name of the modelfile
        modelpath: Path to the modelfile
        parameterfile: Name of file containing parameteres
        parameters: Parameters as a dictionar
        memory_limit: the percentage where the simulation aborts
        """

        self.modelfile = modelfile
        self.modelpath = modelpath
        self.parameterfile = parameterfile
        self.parameters = parameters

        self.supress_output = supress_output

        self.filepath = os.path.abspath(__file__)
        self.filedir = os.path.dirname(self.filepath)


        if self.supress_output:
            self.vdisplay = Xvfb()
            self.vdisplay.start()

        # if memory_threshold:
        #     from memory import Memory
        #     self.memory_report = Memory()
        #     # self.memory_threshold = memory_threshold


        self.clean()


    def __del__(self):
        if mp.current_process().name == "MainProcess":
            self.clean()
            if self.supress_output:
                self.vdisplay.stop()

    def startSupress(self):
        self.supress_output = True
        self.vdisplay = Xvfb()
        self.vdisplay.start()

    def endSupress(self):
        self.supress_output = False
        self.vdisplay.stop()

    def clean(self, process="*"):
        for f in glob.glob("tmp_U_%s.npy" % (process)):
            os.remove(f)

        for f in glob.glob("tmp_t_%s.npy" % (process)):
            os.remove(f)


    def saveParameters(self, new_parameters):
        if os.path.samefile(os.getcwd(), os.path.join(self.filedir, self.modelpath)):
            f = open(self.parameterfile, "w")
        else:
            f = open(self.modelpath + self.parameterfile, "w")

        for parameter in self.parameters.keys():
            if parameter in new_parameters:
                save_parameter = new_parameters[parameter]
            else:
                save_parameter = self.parameters[parameter]

            f.write(parameter + " = " + str(save_parameter) + "\n")

        f.close()


    def run(self, new_parameters={}):
        current_process = mp.current_process().name.split("-")
        if current_process[0] == "PoolWorker":
            current_process = str(current_process[-1])
        else:
            current_process = "0"

        cmd = ["python", "simulation.py", self.modelfile, self.modelpath,
               "--CPU", current_process]

        for parameter in new_parameters:
            cmd.append(parameter)
            cmd.append(str(new_parameters[parameter]))

        simulation = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # TODO Reintroduce this pice of code
        # Note this checks total memory used by all applications
        # if self.memory_threshold:
        #     if self.memory_report.totalPercent() > self.memory_threshold:
        #         print "\nWARNING: memory threshold exceeded, %g > %g" % (self.memory_report.totalPercent(), self.memory_threshold)
        #         print "           aborting simulation"
        #         simulation.terminate()
        #         raise MemoryError("memory threshold exceeded")
        #
        #
        #     time.sleep(self.memory_report.delta_poll)
        #
        ut, err = simulation.communicate()

        if simulation.returncode != 0:
            print "Error when running simulation:"
            print err
            sys.exit(1)

        V = np.load("tmp_U_%s.npy" % current_process)
        t = np.load("tmp_t_%s.npy" % current_process)

        self.clean(current_process)

        return t, V


    def runNoCalculation(self, new_parameters={}):
        pass
