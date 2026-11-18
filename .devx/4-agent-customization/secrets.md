<div class="dx-hero" data-eyebrow="MODULE 04 / SETUP" data-title="Setting up Secrets" data-meta="NEEDS::Spark model key (local)|TIME::3 min"></div>

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right; max-width:300px;margin:25px;" />


For this customization module to work, we will need to configure the NVIDIA API Key. Use the <button onclick="openVoila('code/secrets_management/secrets_management_4.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set this up. Note that the secrets you already set for Modules 1 through 3 should persist here as well. 

You can also launch the Secrets Manager directly from the Jupyterlab launcher.

## Spark Model Key <span class="dx-chip is-green">REQUIRED</span>

This fork runs every model locally on the DGX Spark through the local gateway (`NVIDIA_BASE_URL` in `variables.env`). If you saved the **Spark Model Key** in Module 1, it is already set. Otherwise: in **NVIDIA Sync → Models**, set Network access to **LAN** (stop the model first, switch, then start it again) and copy the API key shown there into the **Spark Model Key** field. No cloud account is needed.

> Using the hosted NVIDIA API instead? Remove `NVIDIA_BASE_URL` from `variables.env`; then the NVIDIA key below becomes required.

## NVIDIA API Key <span class="dx-chip">HOSTED MODE ONLY</span>

NVIDIA API Key provides access to NVIDIA's AI services and models. For this customization module, we will need an API Key to access and customize NVIDIA models.

<details class="dx-peek is-setup">
<summary>⚠️ Don't have an account?</summary>

You can get free non-commercial access to NVIDIA NIMs with an [NVIDIA Developer Account](https://developer.nvidia.com/developer-program).
</details>

<details class="dx-peek is-setup">
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [NGC console](https://org.ngc.nvidia.com/setup/api-keys).

</details>

## Previous API Keys

If you had set these previously, they should persist in the Secrets Manager! These keys are not required for this module. 

<details class="dx-peek is-setup">
<summary>⚠️ Still Want to Set These? Expand Me!</summary>

## Tavily API Key <span class="dx-chip">OPTIONAL · WEB SEARCH</span>

Not needed by default: this fork searches the local IT knowledge base (`WORKSHOP_SEARCH=local`). Set `WORKSHOP_SEARCH=tavily` in `variables.env` and add a key only if you want live web search.

Tavily is a search API designed for AI agents. It provides real-time web search capabilities that help agents gather up-to-date information from the internet.

<details class="dx-peek is-setup">
<summary>⚠️ Don't have an account?</summary>

You can get free access to Tavily with a [Tavily Developer Account](https://tavily.com/).
</details>

<details class="dx-peek is-setup">
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [Tavily Dashboard](https://app.tavily.com/home).

</details>

## LangSmith API Key <span class="dx-chip">OPTIONAL</span>

LangSmith is LangChain's platform for testing, evaluating, and monitoring LLM applications. It provides tracing and debugging capabilities for your AI agents.

<details class="dx-peek is-setup">
<summary>⚠️ Don't have an account?</summary>

You can get free access to LangSmith with a [LangSmith Account](https://smith.langchain.com/).
</details>

<details class="dx-peek is-setup">
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [LangSmith Settings](https://smith.langchain.com/settings).

</details>

</details>

## Ready to Customize!

Once you have your NVIDIA API Key configured, you're ready to start customizing your agents. Continue to [Introduction to Customization](intro_customization.md).
