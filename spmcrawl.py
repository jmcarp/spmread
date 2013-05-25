# 
import os

# Project imports
from spmread import spm_factory

def get_spm_dirs(path):

    return [root for root, dirs, files in os.walk(path) 
        if 'SPM.mat' in files]

def spm_crawl(path):
    
    #
    results = {}

    # Get SPM directories
    spm_dirs = get_spm_dirs(path)

    for spm_dir in spm_dirs:

        spm = spm_factory(os.path.join(spm_dir, 'SPM.mat'))
        results[spm_dir] = spm

    return results
