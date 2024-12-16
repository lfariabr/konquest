from apiCrm.dicts.stores import stores

# Rules to define what is an appointment for aesthetic services = Pró-Corpo
procedures_es = ['AVALIAÇÃO ESTÉTICA', 
                 'AVALIAÇÃO INJETÁVEIS E INVASIVOS']

# Reminders
reminder_desired_status_es = ['Confirmado', 
                              'Agendado']
reminder_undesired_status_es = ['Atendido', 
                                'Falta', 
                                'Cancelado']
stores_include_es = ["JARDINS"] # JARDINS
# store for store in stores

# Reschedule
reschedule_desired_status_es = ['Falta',
                                'Cancelado']
reschedule_undesired_status_es = ['Atendido', 
                                    'Agendado', 
                                    'Confirmado']
reschedule_stores_include_es = ['all']

# NPS
nps_desired_status_es = ['Atendido']
nps_undesired_status_es = ['Falta', 
                            'Cancelado', 
                            'Agendado', 
                            'Confirmado']
nps_stores_include_es = ['all']

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