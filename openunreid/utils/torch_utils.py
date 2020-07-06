from __future__ import absolute_import
import os
import os.path as osp
import warnings
import shutil

import torch
from torch.nn import Parameter

from .file_utils import mkdir_if_missing


def to_numpy(tensor):
    if torch.is_tensor(tensor):
        return tensor.cpu().numpy()
    elif type(tensor).__module__ != 'numpy':
        raise ValueError("Cannot convert {} to numpy array"
                         .format(type(tensor)))
    return tensor


def to_torch(ndarray):
    if type(ndarray).__module__ == 'numpy':
        return torch.from_numpy(ndarray)
    elif not torch.is_tensor(ndarray):
        raise ValueError("Cannot convert {} to torch tensor"
                         .format(type(ndarray)))
    return ndarray


def save_checkpoint(state, is_best, fpath='checkpoint.pth.tar'):
    mkdir_if_missing(osp.dirname(fpath))
    torch.save(state, fpath)
    if is_best:
        shutil.copy(fpath, osp.join(osp.dirname(fpath), 'model_best.pth'))


def load_checkpoint(fpath):
    if osp.isfile(fpath):
        # map to CPU to avoid extra GPU cost
        # checkpoint = torch.load(fpath, map_location=torch.device('cpu'))
        checkpoint = torch.load(fpath)['state_dict']
        checkpoint = checkpoint.load_state_dict()
        print("=> Loaded checkpoint '{}'".format(fpath))
        return checkpoint
    else:
        raise ValueError("=> No checkpoint found at '{}'".format(fpath))

def load_checkpoint_translation(Ga, Gb, cfg):
    fpath = cfg.resume
    Ga.load_state_dict(torch.load(os.path.join(fpath, 'Ga.pth')))
    Gb.load_state_dict(torch.load(os.path.join(fpath, 'Gb.pth')))
    print("=> Loaded checkpoint Ga and Gb  '{}'".format(fpath))

    return Ga, Gb


def copy_state_dict(state_dict, model, strip=None):
    tgt_state = model.state_dict()
    copied_names = set()
    unexpected_keys = set()
    for name, param in state_dict.items():
        if (strip is not None and name.startswith(strip)):
            name = name[len(strip):]
        if (name not in tgt_state):
            unexpected_keys.add(name)
            continue
        if isinstance(param, Parameter):
            param = param.data
        if (param.size() != tgt_state[name].size()):
            warnings.warn('mismatch: {} {} {}'.format(name, param.size(), tgt_state[name].size()))
            continue
        tgt_state[name].copy_(param)
        copied_names.add(name)

    missing = set(tgt_state.keys()) - copied_names
    missing = set([m for m in missing if not m.endswith('num_batches_tracked')])
    if len(missing) > 0:
        warnings.warn("missing keys in state_dict: {}".format(missing))
    if len(unexpected_keys)>0:
        warnings.warn("unexpected keys in checkpoint: {}".format(unexpected_keys))

    return model