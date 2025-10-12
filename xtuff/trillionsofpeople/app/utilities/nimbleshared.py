#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# nimble-ai shared functions

def create_user_interactions():
    try:
        df = pd.read_json('userinteractions.json')
    except:
        print('creating userinteractions.json')
        df = pd.DataFrame()
    return