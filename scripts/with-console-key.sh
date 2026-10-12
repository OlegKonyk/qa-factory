#!/usr/bin/env bash
# Run a command billed to the Console API key instead of the subscription (docs/decisions.md,
# 2026-10-12). The key lives only in this Mac's Keychain, under the service name
# anthropic-console-key; it never enters argv, a file or the output. Store it once with:
#   read -rs "K?Paste key: "; security add-generic-password -U -a "$USER" -s anthropic-console-key -w "$K"; unset K
# The Restate service runs the steps, so start the service under this, not the `run` command.
set -euo pipefail
ANTHROPIC_API_KEY=$(security find-generic-password -a "$USER" -s anthropic-console-key -w)
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "with-console-key: the Keychain entry anthropic-console-key is empty" >&2
  exit 2
fi
export ANTHROPIC_API_KEY
# The key is scoped to the organization, so every request names the workspace it bills.
export ANTHROPIC_CUSTOM_HEADERS="anthropic-workspace-id: ${QA_FACTORY_WORKSPACE:-wrkspc_016pMAGEcBC7SFnV1RxifBSR}"
exec "$@"
