@{
  ExcludeRules = @(
    # Installer and test scripts talk to a human at a console, so Write-Host is intended.
    'PSAvoidUsingWriteHost',
    # The installer's internal helpers honour the script-level -DryRun switch instead of -WhatIf/-Confirm.
    'PSUseShouldProcessForStateChangingFunctions'
  )
}
