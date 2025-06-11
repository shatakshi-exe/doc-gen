#!/bin/bash

SUBSCRIPTION_ID=""
LOCATION=""
MODELS_PARAMETER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --Subscription)
      SUBSCRIPTION_ID="$2"
      shift 2
      ;;
    --Location)
      LOCATION="$2"
      shift 2
      ;;
    --ModelsParameter)
      MODELS_PARAMETER="$2"
      shift 2
      ;;
    *)
      echo "❌ ERROR: Unknown option: $1"
      exit 1
      ;;
  esac
done

AIFOUNDRY_NAME="${AZURE_AIFOUNDRY_NAME}"
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP}"

# Validate required parameters
MISSING_PARAMS=()
[[ -z "$SUBSCRIPTION_ID" ]] && MISSING_PARAMS+=("SubscriptionId")
[[ -z "$LOCATION" ]] && MISSING_PARAMS+=("Location")
[[ -z "$MODELS_PARAMETER" ]] && MISSING_PARAMS+=("ModelsParameter")
[[ -z "$RESOURCE_GROUP" ]] && MISSING_PARAMS+=("AZURE_RESOURCE_GROUP")

if [[ ${#MISSING_PARAMS[@]} -ne 0 ]]; then
  echo "❌ ERROR: Missing required parameters: ${MISSING_PARAMS[*]}"
  echo "Usage: $0 --SubscriptionId <SUBSCRIPTION_ID> --Location <LOCATION> --ModelsParameter <MODELS_PARAMETER>"
  exit 1
fi

# If AI Foundry already exists, skip quota validation
existing=$(az cognitiveservices account show --name "$AIFOUNDRY_NAME" --resource-group "$RESOURCE_GROUP" --query "name" --output tsv 2>/dev/null)
if [[ -n "$existing" ]]; then
  echo "✅ AI Foundry '$AIFOUNDRY_NAME' exists. ⏭️ Skipping quota validation."
  exit 0
else
  echo "❌ AI Foundry '$AIFOUNDRY_NAME' not found. Proceeding with quota validation..."
fi

# Load model deployments
aiModelDeployments=$(jq -c ".parameters.$MODELS_PARAMETER.value[]" ./infra/main.parameters.json)
if [[ $? -ne 0 ]]; then
  echo "❌ ERROR: Failed to parse main.parameters.json. Ensure jq is installed and the JSON is valid."
  exit 1
fi

az account set --subscription "$SUBSCRIPTION_ID"
echo "🎯 Active Subscription: $(az account show --query '[name, id]' --output tsv)"

ALL_REGIONS=('australiaeast' 'eastus2' 'francecentral' 'japaneast' 'norwayeast' 'swedencentral' 'uksouth' 'westus')

declare -A regionAvailabilityMap
declare -a fallbackRegions

# Prioritize selected location first
REGIONS_TO_CHECK=("$LOCATION")
for r in "${ALL_REGIONS[@]}"; do
  [[ "$r" != "$LOCATION" ]] && REGIONS_TO_CHECK+=("$r")
done

# Header
printf "\n%-4s | %-15s | %-40s | %-6s | %-6s | %-9s\n" "No." "Region" "Model Name" "Limit" "Used" "Available"
printf -- "-----------------------------------------------------------------------------------------------\n"

region_idx=1

for region in "${REGIONS_TO_CHECK[@]}"; do
  allModelsFit=true
  regionPrinted=false

  while IFS= read -r deployment; do
    name=$(echo "$deployment" | jq -r '.name')
    model=$(echo "$deployment" | jq -r '.model.name')
    type=$(echo "$deployment" | jq -r '.sku.name')
    capacity=$(echo "$deployment" | jq -r '.sku.capacity')

    result=$(./infra/scripts/validate_model_quota.sh --location "$region" --model "$model" --deployment-type "$type")

    if echo "$result" | jq -e 'has("error")' > /dev/null; then
      echo "⚠️  $(echo "$result" | jq -r '.model') not found in region $region"
      allModelsFit=false
    else
      modelType=$(echo "$result" | jq -r '.model')
      used=$(echo "$result" | jq -r '.used')
      limit=$(echo "$result" | jq -r '.limit')
      available=$(echo "$result" | jq -r '.available')

      if ! $regionPrinted; then
        printf "%-4s | %-15s | %-40s | %-6s | %-6s | %-9s\n" "$region_idx" "$region" "$modelType" "$limit" "$used" "$available"
        regionPrinted=true
      else
        printf "     | %-15s | %-40s | %-6s | %-6s | %-9s\n" "" "$modelType" "$limit" "$used" "$available"
      fi

      [[ "$available" -lt "$capacity" ]] && allModelsFit=false
    fi
  done <<< "$aiModelDeployments"

  if $regionPrinted; then
    printf -- "-----------------------------------------------------------------------------------------------\n"
  fi

  if $allModelsFit; then
    regionAvailabilityMap["$region"]="true"
    if [[ "$region" == "$LOCATION" ]]; then
      echo "✅ Sufficient quota is available in selected region: $LOCATION"
      exit 0
    else
      fallbackRegions+=("$region")
    fi
  fi

  ((region_idx++))
done

# Fallback result
echo -e "\n❌ The selected region '$LOCATION' does not have sufficient quota for all required models."
if [[ ${#fallbackRegions[@]} -gt 0 ]]; then
  echo "➡️  You can try using one of the following regions where all models have sufficient quota:"
  for fallback in "${fallbackRegions[@]}"; do
    echo "   • $fallback"
  done
  echo -e "\n🔧 To proceed, run:"
  echo "    azd env set AZURE_ENV_OPENAI_LOCATION '<region>'"
  echo "📌 To confirm it's set correctly, run:"
  echo "    azd env get-value AZURE_ENV_OPENAI_LOCATION"
  echo "▶️  Once confirmed, re-run azd up to deploy the model in the new region."
  exit 2
else
  echo "❌ No fallback regions found with sufficient quota for all models."
  exit 1
fi
