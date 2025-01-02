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

stores_include_es = ["JARDINS"] # store for store in stores

store_include_pl = ['PLÁSTICA']

# RESCHEDULE RULES
stores_include_es_reschedule = [store for store in stores] # store for store in stores

reschedule_desired_status_es = ['Falta',
                                'Cancelado']
reschedule_undesired_status_es = ['Atendido', 
                                    'Agendado', 
                                    'Confirmado']
reschedule_stores_include_es = ['all']

# NPS RULES
nps_desired_status_es = ['Atendido']
nps_undesired_status_es = ['Falta', 
                            'Cancelado', 
                            'Agendado', 
                            'Confirmado']
nps_stores_include_es = [store for store in stores]

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