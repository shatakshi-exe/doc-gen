#!/bin/bash

SUBSCRIPTION_ID=""
LOCATION=""
MODELS_PARAMETER=""

ALL_REGIONS=('australiaeast' 'eastus2' 'francecentral' 'japaneast' 'norwayeast' 'swedencentral' 'uksouth' 'westus')

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --subscription)
      SUBSCRIPTION_ID="$2"
      shift 2
      ;;
    --location)
      LOCATION="$2"
      shift 2
      ;;
    --models-parameter)
      MODELS_PARAMETER="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate inputs
MISSING_PARAMS=()
[[ -z "$SUBSCRIPTION_ID" ]] && MISSING_PARAMS+=("subscription")
[[ -z "$LOCATION" ]] && MISSING_PARAMS+=("location")
[[ -z "$MODELS_PARAMETER" ]] && MISSING_PARAMS+=("models-parameter")

if [[ ${#MISSING_PARAMS[@]} -gt 0 ]]; then
  echo "❌ ERROR: Missing parameters: ${MISSING_PARAMS[*]}"
  exit 1
fi

az account set --subscription "$SUBSCRIPTION_ID" || exit 1
echo "🎯 Active Subscription: $(az account show --query '[name, id]' --output tsv)"

aiModelDeployments=$(jq -c ".parameters.$MODELS_PARAMETER.value[]" ./infra/main.parameters.json)

declare -A regionAvailabilityMap
declare -a fallbackRegions
printf -- "-----------------------------------------------------------------------------------------------\n"
printf "%-4s | %-15s | %-40s | %-6s | %-6s | %-9s\n" "No." "Region" "Model Name" "Limit" "Used" "Available"
printf -- "-----------------------------------------------------------------------------------------------\n"

region_idx=1

for region in "${ALL_REGIONS[@]}"; do
  allModelsFit=true
  regionPrinted=false

  while IFS= read -r deployment; do
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
    [[ "$region" != "$LOCATION" ]] && fallbackRegions+=("$region")
  fi

  ((region_idx++))
done

# Result Evaluation
if [[ "${regionAvailabilityMap[$LOCATION]}" == "true" ]]; then
  echo "✅ Sufficient quota is available for all models in the selected region: $LOCATION"
  exit 0
else
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
  fi
  exit 1
fi
