import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor
from loguru import logger
from sklearn.metrics import mean_squared_log_error

from src import utils
from src.data import EcuardoSales, transformers

if __name__ == "__main__":
    reg_catboost = CatBoostRegressor(
        n_estimators=200,
        loss_function="RMSE",
        learning_rate=1e-3,
        task_type="CPU",
        random_state=37,
        verbose=False,
        # border_count=128,
    )
    reg_xgb = xgb.XGBRegressor(
        tree_method="hist",
        enable_categorical=True,
        n_estimators=1000,
        max_depth=7,
        eta=0.1,
        subsample=0.7,
    )
    reg_lgb = lgb.LGBMRegressor(
        num_leaves=15,
        max_depth=-1,
        random_state=37,
        silent=True,
        metric="rmse",
        n_jobs=4,
        n_estimators=1000,
        colsample_bytree=0.9,
        subsample=0.9,
        learning_rate=1e-3,
    )

    regressor = reg_xgb

    conf = utils.load_conf()
    data = EcuardoSales(conf["PATH"], diff_order=1)

    pipe_sales = transformers.make_pipeline_sale()

    path_train = "data/processed/train.csv"
    path_val = "data/processed/val.csv"
    df_train_raw = pd.read_csv(path_train, parse_dates=["date"], index_col="id")
    df_val_raw = pd.read_csv(path_val, parse_dates=["date"], index_col="id")

    df = pd.concat((df_train_raw, df_val_raw)).sort_values(by="date")
    df_ = df[(df["family"] == "AUTOMOTIVE") & (df["store_nbr"] == 1)]

    for store, family, Xtrain, ytrain, Xval, yval in data.gen_Xy_trainval(df=df_, deterministic=True):
        # pool_train = Pool(Xtrain, ytrain, cat_features=utils.cat_features)
        # pool_val = Pool(Xval.iloc[1:], yval.iloc[1:], cat_features=utils.cat_features)
        # reg_catboost.fit(pool_train)
        # a = reg_catboost.predict(pool_val)

        regressor.fit(Xtrain, ytrain)
        a = regressor.predict(Xval.iloc[1:])

        pipe_sales.fit(yval)

        pred = np.clip(pipe_sales.inverse_transform(a[:, None]), 0, None)[1:]

        msle = mean_squared_log_error(yval[1:], pred)

        logger.info(f"store: {store} - family: {family} - msle: {msle:.5f}")

        print(yval[1:])
        print(pred)