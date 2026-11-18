<div class="dx-hero" data-eyebrow="MODULE 07 / SETUP" data-title="Two minutes of setup." data-sub="The core lab uses the Spark's local model (or an NVIDIA API key in hosted mode). Optional harnesses need their own setup." data-meta="NEEDS::Spark model key (local)|TIME::2 min"></div>

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right;max-width:240px;margin:20px;" />

Before exploring agent harnesses, let's make sure you have the API key you need for this module. The agents and harnesses in this module run on NVIDIA's models, so you'll need your NVIDIA API Key ready (hosted mode). In this local-first fork they run on the Spark's own model, so the Spark Model Key is all you need.

If you've already set this up in an earlier module, you're good to go — skip straight to the next page.

Use the <button onclick="openVoila('code/secrets_management/secrets_management_7.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set up your API Keys. You can also launch the Secrets Manager directly from the Jupyterlab launcher.

## Spark Model Key <span class="dx-chip is-green">REQUIRED</span>

This fork runs every model locally on the DGX Spark through the local gateway (`NVIDIA_BASE_URL` in `variables.env`). If you saved the **Spark Model Key** in Module 1, it is already set. Otherwise: in **NVIDIA Sync → Models**, set Network access to **LAN** (stop the model first, switch, then start it again) and copy the API key shown there into the **Spark Model Key** field. No cloud account is needed.

> Using the hosted NVIDIA API instead? Remove `NVIDIA_BASE_URL` from `variables.env`; then the NVIDIA key below becomes required.

<details class="dx-peek is-setup">
<summary>Hosted mode only: still need to set up your NVIDIA API Key? Expand for details.</summary>

## NVIDIA API Key <span class="dx-chip">HOSTED MODE ONLY</span>

This key powers the lab’s Nemotron calls and can be reused in the optional Hermes custom-endpoint setup. Claude Code and Codex require their own model access.

NGC is the NVIDIA GPU Cloud. This is the repository for all NVIDIA software, models, and more. For this workshop, we will need an API Key in order to access models.

<details class="dx-peek is-setup">
<summary>Don't have an account?</summary>

You can get free non-commercial access to NVIDIA NIMs with an [NVIDIA Developer Account](https://developer.nvidia.com/developer-program).
</details>

<details class="dx-peek is-setup">
<summary>Don't have an API Key?</summary>

Manage your API Keys from the [NGC console](https://org.ngc.nvidia.com/setup/api-keys).

</details>

</details>

With your Spark Model Key (or, in hosted mode, your NVIDIA API key) configured, you're ready to pop the hood on your agents. Head over to [The Harness Layer](intro_agent_harnesses) to see what's really been running your agents all along.
