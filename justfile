# Wire the hooks and the local folder. Run once after cloning.
setup:
    git config core.hooksPath hooks
    mkdir -p .local/handoff

# The one definition of green.
check:
    scripts/check.sh
