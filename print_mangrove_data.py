from calculate_mangrove_data import Mangrove_data
import pandas as pd

year_list = ['2016','2017','2018','2019','2020','2021']
location_codes = [
    'mamberamo_raya','biak_numfor12','sarmi', #Lagoon
    'mappi','asmat', #Delta
    'intersection_MamberamoRaya_Waropen','supiori', #OpenCoast
    'mamberamo_raya1','teluk_bintuni' #Estuary
]
model ='01-10'

IDR_per_MgC = 75000
USD_to_IDR = 15000
USD_per_MgC = IDR_per_MgC/USD_to_IDR

C_to_CO2 = 44/12


# print("START\n\nCarbon Stock\nCarbon Valuation (USD)\nCarbon Valuation (IDR)")
# for location_idx in range(len(location_codes)):
#     location = location_codes[location_idx]
#     mangrove_data_per_year = Mangrove_data('users/liechristopher7/',location,model,year_list)
#     print(location)
#     for year_idx in range(len(year_list)):
#         year = year_list[year_idx]
#         # print(year+' '+location)
#         print(f"{sum([mangrove_data_per_year.areaSqM_per_class_year[class_name][year_idx] for class_name in mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves]]):.4f}")
        # current_year_mean = mangrove_data_per_year.total_mean_carbon_per_year[year_idx]
        # current_year_stddev = mangrove_data_per_year.total_stddev_carbon_per_year[year_idx]
        # valuation_USD_mean = current_year_mean*(C_to_CO2)*USD_per_MgC
        # valuation_USD_stddev = current_year_stddev*(C_to_CO2)*USD_per_MgC
        # valuation_IDR_mean = valuation_USD_mean*IDR_per_MgC
        # valuation_IDR_stddev = valuation_USD_stddev*IDR_per_MgC
        # print(f"{current_year_mean:,.4f} ± {current_year_stddev:,.4f} MgC\tUSD {valuation_USD_mean:,.2f} ± {valuation_USD_stddev:,.2f}\tIDR {valuation_IDR_mean:,.2f} ± {valuation_IDR_stddev:,.2f}")

        # print({
        #     'Category': mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves],
        #     'Mean': [mangrove_data_per_year.mean_carbon_per_class_year[class_name][year_idx] for class_name in mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves]],
        #     'Standard Deviation': [mangrove_data_per_year.stddev_carbon_per_class_year[class_name][year_idx] for class_name in mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves]]
        # })

        # print(
        #     [f'{name}: {mangrove_data_per_year.areaSqM_per_class_year[name][year_idx]:.4f} m^2'
        #               for name in mangrove_data_per_year.class_list]
        # )
    # break

medians = [13114294.4463, 14936920.9766, 9776785.5733, 3645866.6668, 14696972.1287, 28250073.2417, 7528107.1144, 70290985.4402, 23228739.3606]
for median in medians:
    current_year_mean = median*1.087/1000
    current_year_stddev = median*0.584/1000
    valuation_USD_mean = current_year_mean*(C_to_CO2)*USD_per_MgC
    valuation_USD_stddev = current_year_stddev*(C_to_CO2)*USD_per_MgC
    valuation_IDR_mean = valuation_USD_mean*IDR_per_MgC
    valuation_IDR_stddev = valuation_USD_stddev*IDR_per_MgC
    # print(f"{int(current_year_mean):,} ± {int(current_year_stddev):,}\\t{int(round(valuation_USD_mean,-3)):,} ± {int(round(valuation_USD_stddev,-3)):,}\\t{int(round(valuation_IDR_mean,-6)):,} ± {int(round(valuation_IDR_stddev,-6)):,}")
    print(f"{current_year_mean:,} ± {current_year_stddev:,}\\t{valuation_USD_mean:,.2f} ± {int(round(valuation_USD_stddev,-3)):,}\\t{int(round(valuation_IDR_mean,-6)):,} ± {int(round(valuation_IDR_stddev,-6)):,}")
    # print(f"{int(current_year_mean):,} ± {int(current_year_stddev):,} MgC\\tUSD {int(round(valuation_USD_mean,-3)):,} ± {int(round(valuation_USD_stddev,-3)):,}\\tIDR {int(round(valuation_IDR_mean,-6)):,} ± {int(round(valuation_IDR_stddev,-6)):,}")

print("\n\nEND")