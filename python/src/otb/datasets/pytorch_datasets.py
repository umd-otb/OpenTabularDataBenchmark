import os
from functools import cached_property

import numpy as np
import requests
import torch
from torch.utils.data import Dataset

from .utils import google_drive_download_link

# TODO: replace this with an actual data file instead of in code
"""
URLs (and, later, possibly other metadata) for each non-CIFAR dataset.

Note: these ids do not need to be updated if a new version is uploaded to the drive,
only if the file is completely "changed" (i.e. Google is treating it like a different
file).
"""
data_urls = {
    'arcene': google_drive_download_link('1cnuQwVtQ-FsJ_En9_ln2KU0n30wJ4ffe'),
    'covertype': google_drive_download_link('1ixC-jAgdAgPnCL37uaTEnBep7q43liNP'),
    'higgs': google_drive_download_link('1mz6E-5eV5ThnzdbimvTTeTTGSoJTjS_I'),
    'poker': google_drive_download_link('1yVdp4pHSmrFasHhX4j4vtxVHYHUvciun'),
    'sarcos': google_drive_download_link('1Nr7MIWogLo0aY_uQdSCSfGysMr5Wswq5'),
}


def _download_datafile(source_url, dest_path, download=True):
    """
    Ensures that the file (the NPZ archive) exists (will download if the destination
    file does not exist and `download` is True).
    
    Args:
        source_url: download url (should be a google drive download link)
        dest_path: full path of the destination file
        download: whether to download if not present (will error if data is not already present)
    """
    
    if os.path.exists(dest_path):
        print(f'Data already available at `{dest_path}`')
    elif download:
        print(f'Downloading data from `{source_url}` into `{dest_path}`')
        r = requests.get(source_url, stream=True)
        
        if r.status_code != requests.codes.ok:
            r.raise_for_status()
            raise RuntimeError(f'unable to download file from `{source_url}`')
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        declared_file_size = int(r.headers.get('Content-Length', 0))
        
        with open(dest_path, 'wb') as output_file:
            output_file.write(r.content)
    else:
        raise ValueError('Data files don\'t exist but not instructed to download')
    

def _load_data(data_dir, name, download=True):
    name = name.lower()
    if name not in data_urls:
        raise ValueError(f'dataset with name `{name}` not recognized')
    
    # load data files (download if not present)
    data_filename = os.path.join(data_dir, f'{name}.npz')
    _download_datafile(data_urls[name], data_filename, download)
    
    return np.load(data_filename)


class OpenTabularDataset(Dataset):
    """
    A tabular dataset from the benchmark (except for the CIFAR10, which is
    accessible in tabular form using `TabularCIFAR10Dataset`).
    """
    
    def __init__(self, data_dir, name, split='train', download=True, transform=None):
        self.data = _load_data(data_dir, name, download=download)
        self.inputs, self.outputs = self._extract_split(self.data, split)

        # convert data to torch tensors
        self.X = torch.from_numpy(self.inputs)
        self.y = torch.from_numpy(self.outputs)
        
        self.data_dir = data_dir
        self.name = name
        self.split = split
        self.transform = transform

    def _extract_split(self, data, split):
        if split not in self.splits:
            raise ValueError(f'dataset `{self.name}` does not have a `{split}` split')
    
        # return requested split
        return data[f'{split}-data'], data[f'{split}-labels']

    def __len__(self):
        return self.X.size(0)

    def __getitem__(self, idx):
        inputs = self.X[idx, :]
        outputs = self.y[idx].item() if self.y[idx].numel() == 1 else self.y[idx]
        example_pair = (inputs, outputs)
        
        # apply transforms if there are any to the input-output pair
        return self.transform(example_pair) if self.transform else example_pair

    @cached_property
    def splits(self):
        return {filename.partition('-')[0] for filename in self.data.files
                if '-' in filename and not filename.startswith('_')}

    @cached_property
    def input_attributes(self):
        return self.data['_columns-data']
    
    @cached_property
    def output_attributes(self):
        return self.data['_columns-labels']
    
    def dataframe(self):
        import pandas as pd

        combined = np.hstack((
            self.inputs,
            np.expand_dims(self.outputs, -1) if self.inputs.ndim == self.outputs.ndim + 1 else self.outputs
        ))
        all_columns = np.hstack((self.data['_columns-data'], self.data['_columns-labels']))

        return pd.DataFrame(data=combined, columns=all_columns)

    def numpy(self):
        return self.inputs, self.outputs

