import joblib
import json

MODEL_PATH = "src/xgb_model.pkl"

print("=" * 60)
print("Loading model")
print("=" * 60)

model = joblib.load(MODEL_PATH)

print("\nMODEL TYPE:")
print(type(model))

print("\nNUMBER OF FEATURES:")
print(model.num_features())

print("\nFEATURE NAMES:")
try:
    print(model.feature_names)
except Exception as e:
    print("Could not read:", e)

print("\nBOOSTER TYPE:")
print(model.__class__.__name__)

print("\nNUMBER OF TREES:")
try:
    print(model.num_boosted_rounds())
except Exception as e:
    print("Could not read:", e)

print("\nOBJECTIVE:")
try:
    print(model.attr("objective"))
except Exception as e:
    print("Could not read:", e)

print("\nATTRIBUTES:")
try:
    print(model.attributes())
except Exception as e:
    print("Could not read:", e)

print("\nCONFIG:")
try:
    config = json.loads(model.save_config())
    print(json.dumps(config, indent=2))
except Exception as e:
    print("Could not read config:", e)

print("\nDUMPING FIRST TREE:")
try:
    trees = model.get_dump(with_stats=True)
    print(trees[0])
except Exception as e:
    print("Could not dump tree:", e)