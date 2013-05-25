# Imports
import os
import re
import inspect

# Science imports
import numpy as np
import scipy.io as sio
import nibabel as nib

def one_or_list(fun):
    def decorated(*args, **kwargs):
        val = fun(*args, **kwargs)
        val = list(val)
        print val
        if len(val) == 1:
            return val[0]
        return val
    return decorated

def spm_factory(fname):
    
    # Get path
    path = os.path.split(fname)[0]

    # Read SPM.mat
    _mat = sio.loadmat(fname)
    
    # Crash if no 'SPM' substruct
    if 'SPM' not in _mat:
        raise Exception('Bad SPM.mat: No SPM variable')
    
    # Extract relevant data
    mat = _mat['SPM'][0,0]

    # Create appropriate SPMMAT class
    if 'Sess' in mat.dtype.names:
        return SPMMAT1(path, mat)
    else:
        return SPMMAT2(path, mat)

class SPMMAT(object):
    
    @staticmethod
    def flatten_gen(struct):
        '''
        '''
        
        if type(struct) == np.ndarray:
            for substruct in struct:
                for item in SPMMAT.flatten_gen(substruct):
                    yield item
        else:
            yield struct
    
    @staticmethod
    @one_or_list
    def flatten(struct):
        return list(SPMMAT.flatten_gen(struct))

    def __init__(self, path, mat):
        '''
        '''
        
        self.path = path
        self.mat = mat

    def read_all(self):
        
        # Get _read* methods
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        methods = [m for m in methods if m[0].startswith('_read')]
        
        # Initialize result
        result = {}
        
        # Apply methods
        for method in methods:
            value = method[1]()
            if type(value) == dict:
                result.update(value)
            else:
                key = re.sub('_read_', '', method[0])
                result[key] = value
        
        # Return result
        return result

    def get_image(self, contrast, key):
        
        try:
            img = nib.load('%s/%s' % (self.path, contrast[key]))
            contrast['%s_image' % (key)] = img
        except:
            pass

    def _read_nscan(self):
        
        nscan = self.flatten(self.mat['nscan'])
        if hasattr(nscan, '__iter__'):
            return nscan[0]
        return nscan

    def _read_spmid(self):
        
        return self.flatten(self.mat['SPMid'])
    
    def _read_swd(self):
        
        return self.flatten(self.mat['swd'])

    def _read_descrip(self):
        
        return self.flatten(self.mat['xY'][0][0]['VY'][0]['descrip'])

class SPMMAT1(SPMMAT):
    
    def _read_autocorr(self):
        
        return self.flatten(self.mat['xVi'][0]['form'])
    
    def _read_motreg(self):
        
        patterns = [
            'pitch',
            'roll',
            'yaw',
        ]

        regressors = SPMMAT.flatten(self.mat['Sess'][0][0]['C'][0][0]['name'])
        for regressor in regressors:
            for pattern in patterns:
                if re.search(pattern, regressor, re.I):
                    return True
        return False


    def _read_design(self):
        
        # Get design object
        _xsdes = self.flatten(self.mat['xsDes'])
        
        # Get design features

        basis = self.flatten(_xsdes['Basis_functions'])

        nsess = self.flatten(_xsdes['Number_of_sessions'])

        rt = self.flatten(_xsdes['Interscan_interval'])
        rt = re.sub('\s*{.*?}', '', rt)

        hpf = self.flatten(_xsdes['High_pass_Filter'])
        hpf = re.sub('\s*{.*?}', '', hpf, flags=re.I)
        hpf = re.sub('cutoff:\s*', '', hpf, flags=re.I)

        norm = self.flatten(_xsdes['Global_normalisation']).lower()
        
        # Return features
        _locals = locals()
        return {k : _locals[k] for k in _locals 
            if not k.startswith('_') and k != 'self'}

class SPMMAT2(SPMMAT):
    
    def _read_des(self):
        
        return self.flatten(self.mat['xsDes'][0]['Design'])

    def _read_contrasts(self):
        
        # 
        xcon = self.mat['xCon']
        
        # 
        ncon = len(xcon['name'][0])
        
        # Initialize contrasts
        contrasts = []

        # 
        for conidx in range(ncon):
            
            # Extract contrast fields
            contrast = {
                'name' : self.flatten(xcon['name'][0][conidx]),
                'stat' : self.flatten(xcon['STAT'][0][conidx]),
                'eidf' : self.flatten(xcon['eidf'][0][conidx]),
                'con_file' : self.flatten(xcon['Vcon'][0][conidx]['fname']),
                'spm_file' : self.flatten(xcon['Vspm'][0][conidx]['fname']),
                'descrip' : self.flatten(xcon['Vcon'][0][conidx]['descrip']),
            }

            # Link to images
            self.get_image(contrast, 'con_file')
            self.get_image(contrast, 'spm_file')
            
            # Append to contrasts
            contrasts.append(contrast)
        
        # Return completed contrasts
        return contrasts
