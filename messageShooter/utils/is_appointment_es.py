from apiCrm.dicts.stores import stores

procedures_es = ['AVALIAÇÃO ESTÉTICA', 
                 'AVALIAÇÃO INJETÁVEIS E INVASIVOS']

procedures_pl = ['AVALIAÇÃO MAMOPLASTIA',
                'AVALIAÇÃO PLÁSTICA DE ABDÔMEN',
                'AVALIAÇÃO MAMOPLASTIA COM PRÓTESE',
                'AVALIAÇÃO LIPOASPIRAÇÃO',
                'AVALIAÇÃO PRÓTESE DE MAMA',
                'AVALIAÇÃO RINOPLASTIA',
                'AVALIAÇÃO BLEFAROPLASTIA',
                'AVALIAÇÃO RITIDOPLASTIA',
                'AVALIAÇÃO CIRURGIA ÍNTIMA',
                'SEGUNDA OPINIÃO (AVALIAÇÃO CIRURGIA)']

# REMINDER RULES
reminder_desired_status_es = ['Confirmado', 
                              'Agendado']

reminder_undesired_status_es = ['Atendido', 
                                'Falta', 
                                'Cancelado',
                                'Reagendado']

reminder_stores_include_es = ['JARDINS'] # store for store in stores
reminder_stores_include_ipiranga = ['IPIRANGA']
reminder_stores_include_santo_amaro = ['SANTO AMARO']

store_include_pl = ['PLÁSTICA']

# REMINDER RULES - PLÁSTICA
reminder_desired_status_pl = ['Confirmado', 
                              'Agendado']

reminder_undesired_status_pl = ['Atendido', 
                                'Falta', 
                                'Cancelado',
                                'Reagendado']

# RESCHEDULE RULES
stores_include_es_reschedule = [store for store in stores] # store for store in stores
reschedule_stores_include_es = ['all']

reschedule_desired_status_es = ['Falta',
                                'Cancelado']
reschedule_undesired_status_es = ['Atendido', 
                                    'Agendado', 
                                    'Confirmado']

# RESCHEDULE RULES - PLÁSTICA
stores_include_pl_reschedule = ['PLÁSTICA']
reschedule_stores_include_pl = ['PLÁSTICA']

reschedule_desired_status_pl = ['Falta',
                                'Cancelado']
reschedule_undesired_status_pl = ['Atendido', 
                                    'Agendado', 
                                    'Confirmado']

# NPS RULES
nps_stores_include_es = [store for store in stores]

nps_desired_status_es = ['Atendido']
nps_undesired_status_es = ['Falta', 
                            'Cancelado', 
                            'Agendado', 
                            'Confirmado']

# Stores:
stores_exclude_es = ['PRAIA GRANDE', 
                     'HOMA', 
                     'PLÁSTICA']


# Useful intervals:
intervals_es = {
    '-1': 'd1',
    '-2': 'd2',
    '-3': 'd3',
    '-4': 'd4',
    '-5': 'd5',
    '1': 'dMaisum'
}

# interval_time = input - today()