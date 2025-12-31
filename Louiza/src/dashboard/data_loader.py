"""
Data loader for dashboard
Loads and normalizes data from repo
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, Optional, Tuple
from pathlib import Path

# Data directory constant
DATA_DIR = Path(__file__).parent.parent.parent
DATA_CSV_DIR = DATA_DIR / 'data'
SIMULATIONS_DIR = DATA_DIR / 'simulations'
PHASE4_SIGNALS_DIR = DATA_DIR / 'phase4_output' / 'signals'


def load_products() -> pd.DataFrame:
    """Load products data"""
    path = DATA_CSV_DIR / 'products.csv'
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df


def load_segments() -> pd.DataFrame:
    """Load segments data"""
    path = DATA_CSV_DIR / 'segments.csv'
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df


def load_contexts() -> pd.DataFrame:
    """Load contexts data"""
    path = DATA_CSV_DIR / 'contexts.csv'
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df


def load_intent_logs() -> pd.DataFrame:
    """Load historical intent logs"""
    path = DATA_CSV_DIR / 'intent_logs.csv'
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
    return df


def load_simulation_trajectories() -> pd.DataFrame:
    """Load Phase 3 simulation trajectories"""
    path = SIMULATIONS_DIR / 'intent_trajectories.csv'
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
    return df


def load_phase4_anchored() -> pd.DataFrame:
    """Load Phase 4 anchored data"""
    path = SIMULATIONS_DIR / 'phase4_anchored.csv'
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
    return df


def load_intent_index() -> pd.DataFrame:
    """Load intent index signal"""
    path = PHASE4_SIGNALS_DIR / 'intent_index.csv'
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df


def load_momentum() -> pd.DataFrame:
    """Load momentum signals"""
    path = PHASE4_SIGNALS_DIR / 'momentum_7d.csv'
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df


def load_all_data() -> Dict[str, pd.DataFrame]:
    """Load all available data"""
    return {
        'products': load_products(),
        'segments': load_segments(),
        'contexts': load_contexts(),
        'intent_logs': load_intent_logs(),
        'trajectories': load_simulation_trajectories(),
        'phase4_anchored': load_phase4_anchored(),
        'intent_index': load_intent_index(),
        'momentum': load_momentum()
    }

