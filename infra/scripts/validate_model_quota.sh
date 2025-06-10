#!/bin/bash

LOCATION=""
MODEL=""
DEPLOYMENT_TYPE="Standard"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --location)
      LOCATION="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --deployment-type)
      DEPLOYMENT_TYPE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check required parameters
if [[ -z "$LOCATION" || -z "$MODEL" || -z "$DEPLOYMENT_TYPE" ]]; then
  echo "❌ Missing parameters"
  exit 1
fi

MODEL_TYPE="OpenAI.${DEPLOYMENT_TYPE}.${MODEL}"

MODEL_INFO=$(az cognitiveservices usage list --location "$LOCATION" --query "[?name.value=='$MODEL_TYPE']" --output json 2>/dev/null)

if [[ -n "$MODEL_INFO" && "$MODEL_INFO" != "[]" ]]; then
  CURRENT=$(echo "$MODEL_INFO" | jq -r '.[0].currentValue // 0' | cut -d'.' -f1)
  LIMIT=$(echo "$MODEL_INFO" | jq -r '.[0].limit // 0' | cut -d'.' -f1)
  AVAILABLE=$((LIMIT - CURRENT))
  jq -n --arg model "$MODEL_TYPE" --arg region "$LOCATION" \
        --argjson limit "$LIMIT" --argjson used "$CURRENT" --argjson available "$AVAILABLE" \
        '{model: $model, region: $region, limit: $limit, used: $used, available: $available}'
else
  jq -n --arg model "$MODEL_TYPE" --arg region "$LOCATION" \
        '{model: $model, region: $region, error: "Model not available in region"}'
fi
