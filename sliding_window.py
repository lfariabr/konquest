import time

array = ["Vendedora 1 sobrenome: R$ 1000", 
        "Vendedora outro nome: R$ 2000", 
        "Vendedora com ainda outro nome: R$ 3000"]

# advertisement_area = {}

# for right in range(len(array)):

#     advertisement_area[f"Vendedora {right+1}"] = array[right]
#     print(f"Atualizando em {right+1}/{len(array)}...")
#     print(advertisement_area)
#     time.sleep(2)

aggreagated_array = []
for item in array:
    aggreagated_array.append(item)
    print(aggreagated_array)
    print(item)
    for index in range(1, len(item) + 1):

    #     # Exibindo o progresso letra por letra
    #     partial_aggregated_array = aggreagated_array[:-1] + [item[:index]]
    #     print(f"{partial_aggregated_array}")
    #     time.sleep(0.5)

    # print(f"Finalizando... \n{aggreagated_array}")