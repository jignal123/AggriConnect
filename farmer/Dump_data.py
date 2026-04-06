import os
import pandas as pd
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aggriconnect.settings')
django.setup()
from .models import (
    StateMaster,
    MarketMaster,
    CommodityMaster,
    VarietyMaster,
    DistrictMaster,
    GradeMaster,
)
from django.db import connection

if __name__ == "__main__":
    print("Reading....")
    file = os.path.join(
        os.path.dirname(__file__), "..", "dataset", "master_aggriculture_dataset.csv"
    )

    df = pd.read_csv(
        file,
        usecols=["STATE", "district", "Market Name", "Commodity", "Variety", "Grade"],
    )

    states = df["STATE"].unique()
    districts = df["district"].unique()
    market_names = df["Market Name"].unique()
    commodity = df["Commodity"].unique()
    variety = df["Variety"].unique()
    grade = df["Grade"].unique()

    try :
        print("Truncating....")
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE farmer_statemaster;")
            cursor.execute("TRUNCATE TABLE farmer_districtmaster;")
            cursor.execute("TRUNCATE TABLE farmer_marketmaster;")
            cursor.execute("TRUNCATE TABLE farmer_commoditymaster;")
            cursor.execute("TRUNCATE TABLE farmer_varietymaster;")
            cursor.execute("TRUNCATE TABLE farmer_grademaster;")

        states_list = [StateMaster(state_name=st) for st in states]
        districts_list = [DistrictMaster(district_name=dist) for dist in districts]
        market_names_list = [MarketMaster(market_name=mn) for mn in market_names]
        commodity_list = [CommodityMaster(commodity_name=cm) for cm in commodity]
        variety_list = [VarietyMaster(variety_name=vn) for vn in variety]
        grade_list = [GradeMaster(grade_name=gn) for gn in grade]
        
        print("Inserting....")
        StateMaster.objects.bulk_create(states_list)
        DistrictMaster.objects.bulk_create(districts_list)
        MarketMaster.objects.bulk_create(market_names_list)
        CommodityMaster.objects.bulk_create(commodity_list)
        VarietyMaster.objects.bulk_create(variety_list)
        GradeMaster.objects.bulk_create(grade_list)
        print("Completed!!!")
    except Exception as e:
        print("Error ..",e)