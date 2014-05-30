#! /usr/bin/env python
#
# PID.py
#
# Performs the particle ID step of sorting the event map templates
# of the previous stage into tracks vs. cascades. Some fraction of
# CC events is identified as tracks, all others are cascades.
#
# author: Timothy C. Arlen
#         tca3@psu.edu
# author: Sebastian Boeser
#         sboeser@physik.uni-bonn.de
#
# date:   April 10, 2014
#

import logging
from argparse import ArgumentParser, RawTextHelpFormatter
from pisa.utils.utils import set_verbosity,get_binning,check_binning,get_bin_centers
from pisa.utils.jsons import from_json,to_json
from pisa.utils.proc import report_params, get_params, add_params
from pisa.pid.PIDService import PIDService
import numpy as np
import scipy.stats


def get_pid_maps(reco_events,pid_service,**kwargs):
    '''
    Takes the templates of reco_events in form of:
      'nue_cc': map
      'numu_cc': map
      'nutau_cc': map
      'nuall_nc': map
    And applies PID returning a dictionary of events in form of:
      {'trk': {'ebins':ebins,'czbins':czbins,'map':map},
       'csc': {'ebins':ebins,'czbins':czbins,'map':map}}
    '''

    #Be verbose on input
    params = get_params()
    report_params(params, units = [])
    
    #Initialize return dict
    ebins, czbins = get_binning(reco_events)
    reco_events_pid = { 'trck': {'map':np.zeros_like(reco_events['nue_cc']['map']),
                                 'czbins':czbins,
                                 'ebins':ebins},
                        'cscd': {'map':np.zeros_like(reco_events['nue_cc']['map']),
                                 'czbins':czbins,
                                 'ebins':ebins},
                        'params': add_params(params,reco_events['params']),
                      }
    

        
    pid_dict = pid_service.get_maps()

    flavours = ['nue_cc','numu_cc','nutau_cc','nuall_nc']
    for flav in flavours:
        event_map = reco_events[flav]['map']
        
        to_trck_map = event_map*pid_dict[flav]['trck']
        to_cscd_map = event_map*pid_dict[flav]['cscd']
        
        reco_events_pid['trck']['map'] += to_trck_map
        reco_events_pid['cscd']['map'] += to_cscd_map
        
    return reco_events_pid


if __name__ == '__main__':

    #Only show errors while parsing 
    set_verbosity(0)
    parser = ArgumentParser(description='Takes a reco event rate file '
                            'as input and produces a set of reconstructed templates '
                            'of tracks and cascades.',
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('reco_event_maps',metavar='RECOEVENTS',type=from_json,
                        help='''JSON reco event rate file with following parameters:
      {"nue_cc": {'czbins':[...], 'ebins':[...], 'map':[...]}, 
       "numu_cc": {...},
       "nutau_cc": {...},
       "nuall_nc": {...} }''')
    parser.add_argument('pid_dict',metavar='WEIGHTFILE',type=from_json,
                        help='''json file containing parameterizations of the particle ID for each event type.''')
    parser.add_argument('-o', '--outfile', dest='outfile', metavar='FILE', type=str,
                        action='store',default="pid.json",
                        help='''file to store the output''')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='''set verbosity level''')
    args = parser.parse_args()

    #Set verbosity level
    set_verbosity(args.verbose)

    #Check binning
    ebins, czbins = check_binning(args.reco_event_maps)

    #Initialize the PID service
    pid_service = PIDService(args.pid_dict, ebins, czbins)

    #Galculate event rates after PID
    event_rate_pid = get_pid_maps(args.reco_event_maps,pid_service)
    
    logging.info("Saving output to: %s"%args.outfile)
    to_json(event_rate_pid,args.outfile)
    
    