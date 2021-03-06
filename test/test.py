################################################################################
# Copyright (C) 2016 Advanced Micro Devices, Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell cop-
# ies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IM-
# PLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNE-
# CTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
################################################################################

import argparse
import os
import sys
import subprocess
import glob
import multiprocessing
import tempfile
import contextlib
import shutil

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
TENSILE_PATH = os.path.dirname(SCRIPT_PATH)
TEST_PATH = os.path.join(TENSILE_PATH, 'test')
PROBLEMS_PATH = os.path.join(TEST_PATH, 'problems')
SIMPLE_PATH = os.path.join(TEST_PATH, 'simple')

def which(p, paths=None):
    exes = [p+x for x in ['', '.exe', '.bat']]
    for dirname in list(paths or [])+os.environ['PATH'].split(os.pathsep):
        for exe in exes:
            candidate = os.path.join(os.path.expanduser(dirname), exe)
            if os.path.exists(candidate):
                return candidate
    raise Exception('Cannot find ' + p)

def cmd(args, **kwargs):
    print args
    subprocess.check_call(args, env=os.environ, **kwargs)

def cmake(args, **kwargs):
    cmd([which('cmake')] + args, **kwargs)

def build(p, defines=None, prefix=None, target=None, generator=None):
    with tempdir() as build_path:
        cmake_args = [p]
        if generator: cmake_args.append('-G ' + args.generator)
        if prefix: 
            cmake_args.append('-DCMAKE_INSTALL_PREFIX='+prefix)
            cmake_args.append('-DCMAKE_PREFIX_PATH='+prefix)

        for d in defines or []:
            cmake_args.append('-D{0}'.format(d))
        cmake(cmake_args, cwd=build_path)

        build_args = ['--build', build_path, '--config', 'Release']
        if target: build_args.extend(['--target', target])
        if os.path.exists(os.path.join(build_path, 'Makefile')):
            build_args.extend(['--', '-j', str(multiprocessing.cpu_count())])
        cmake(build_args)


def mkdir(*ps):
    p = os.path.join(*ps)
    if not os.path.exists(p): os.makedirs(p)
    return p

@contextlib.contextmanager
def tempdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

if __name__ == "__main__":
    # arguments
    ap = argparse.ArgumentParser(description="TensileTest")
    ap.add_argument('-D', '--define', nargs='+', default=[])
    ap.add_argument('-G', '--generator', default=None)
    ap.add_argument("--backend", "-b", dest="backend", required=True)
    ap.add_argument("--no-validate", dest="validate", action="store_false")
    ap.add_argument("--problem-set", dest="problemSet", choices=["quick", "full"], default="full" )
    ap.set_defaults(validate=True)

    args = ap.parse_args(args=sys.argv[1:])
    validateArgs = []
    if args.validate:
      validateArgs = ["--validate"]
    
    backend = None
    if args.backend.lower() in ["opencl_1.2", "opencl", "cl"]: backend = 'OpenCL_1.2'
    elif args.backend.lower() == "hip": backend = 'HIP'

    with tempdir() as d:
        build_path = os.path.join(d, '_tensile_build')
        solutions_path = os.path.join(d, 'solutions')
        install_path = os.path.join(d, 'usr')
        problems_path = os.path.join(PROBLEMS_PATH,args.problemSet)

        #install tensile
        build(TENSILE_PATH, generator=args.generator, prefix=install_path, defines=args.define, target='install')
        # Run benchmark
        tensileExe = 'tensile.bat'
        if os.name == "posix":
          tensileExe = 'tensile'
        cmd([os.path.join(install_path, 'bin', tensileExe), 'benchmark', '-b', backend, '-p', problems_path, '-s', solutions_path, "-B", build_path]+validateArgs)
        # Build library
        library_args = ['Tensile_SOLUTIONS='+solutions_path, 'Tensile_BACKEND='+backend]
        build(SIMPLE_PATH, generator=args.generator, prefix=install_path, defines=args.define+library_args)

