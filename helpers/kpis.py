import numpy as np
import pandas as pd

from helpers import dataservice_utils

from constants import CRITICAL_MINERALS


def filter_df_critical_minerals(df, key):
    return df


def filter_df_threshold(df, threshold_prct=0.025):
    df["total"] = df["total"].astype(int)
    total_inv_count = df["total"].sum()
    threshold = threshold_prct * total_inv_count
    df["comm_updated"] = np.where(
        df["total"] < threshold, "others", df["commodity_label"]
    )
    df = df.groupby("comm_updated")["total"].sum().reset_index()
    return df


def get_mineral_inventories_count_by_commodity():
    """a helper function to fetch mineral inventories from SPARQL endpoint"""

    df = pd.DataFrame(
        dataservice_utils.fetch_api_data(
            "/mineral-inventories/count-by-commodity", ssl_flag=False
        )
    )
    df = filter_df_critical_minerals(df=df, key="name")
    df = filter_df_threshold(df)
    return {
        "labels": df["comm_updated"].to_list(),
        "values": df["total"].to_list(),
    }


def get_mineral_site_count_per_commodity():
    """a helper function to fetch mineral site count from SPARQL endpoint"""
    df = pd.DataFrame(
        dataservice_utils.fetch_api_data(
            "/mineral-sites/count-by-commodity", ssl_flag=False
        )
    )
    df = filter_df_critical_minerals(df=df, key="name")
    df = filter_df_threshold(df)
    return {
        "labels": df["comm_updated"].to_list(),
        "values": df["total"].to_list(),
    }


def get_docs_per_commodity():
    """a helper function to fetch mineral site count from SPARQL endpoint"""
    df = pd.DataFrame(
        dataservice_utils.fetch_api_data(
            "/documents/count-by-commodity", ssl_flag=False
        )
    )
    df = filter_df_critical_minerals(df=df, key="name")
    df = filter_df_threshold(df)
    return {
        "labels": df["comm_updated"].to_list(),
        "values": df["total"].to_list(),
    }


def get_documents_count():
    df = dataservice_utils.fetch_api_data("/documents/count", ssl_flag=False)
    return df["total"]


def get_inventory_count():
    """a helper function to fetch the inventory count from SPARQL endpoit"""
    df = dataservice_utils.fetch_api_data("/mineral-inventories/count", ssl_flag=False)
    return df["total"]


def get_mineral_site_count():
    """a helper function to fetch mineral site count from SPARQL endpoint"""
    df = dataservice_utils.fetch_api_data("/mineral-sites/count", ssl_flag=False)
    return df["total"]


def get_commodities():
    """a helper function to fetch commodities from SPARQL endpoint"""
    df = pd.DataFrame(
        dataservice_utils.fetch_api_data(
            "/commodities", params={"is_critical": "true"}, ssl_flag=False
        )
    )
    return sorted(df["name"].to_list() + ["REE", "HEAVY-REE", "LIGHT-REE", "PGE"])


def get_commodity_dict():
    df = pd.DataFrame(
        dataservice_utils.fetch_api_data(
            "/commodities", params={"is_critical": "true"}, ssl_flag=False
        )
    )
    commodity_dict = (
        df.set_index(df["uri"].str.split("/").str[-1])["name"].str.lower().to_dict()
    )
    return commodity_dict


if __name__ == "__main__":
    print(get_mineral_inventories_count_by_commodity())
