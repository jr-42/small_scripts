from more_itertools import consecutive_groups
from typing import List

def continuous_interval_with_tol(value_list: List, tol: int): 
    """
    Yields continuous intervals in a list of numbers
    allowing for a tolerance of tol timesteps

    usagge: intervals = list(continuous_interval_with_tol(listofnumbers, tolerance))
    """
    res = [] 
    last = value_list[0] 
    for ele in value_list: 
        if ele-last > tol: 
            yield res 
            res = [] 
        res.append(ele) 
        last = ele 
    yield res 

def continuous_interval(value_list: List) -> List[List]: 

    """ Returns a list of lists containing the set of continuous intervals in value_list"""
    
    return [list(i) for i in consecutive_groups(value_list)]