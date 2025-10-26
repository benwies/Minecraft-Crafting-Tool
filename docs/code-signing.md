# Code signing

This project supports optional code signing for the Windows artifacts. Signing improves integrity and shows a publisher name, but SmartScreen reputation is separate and may still warn until reputation builds or a publicly trusted certificate is used.

## What gets signed

- App executable: `dist/MCCraftingCalculator/MCCraftingCalculator.exe`
- Installer: `dist/installer/MCCraftingCalculator-Setup.exe` (signed post-compile)
- Note: The portable ZIP itself is not a PE file and cannot be Authenticode-signed; the EXE inside the ZIP is signed.

## Certificate options

- Self-signed (development/testing): Fast to create and free. Shows your publisher name but is not trusted by other machines unless they install your certificate. SmartScreen will still warn for most users.
- Publicly trusted (recommended for distribution): Purchase an Organization Validation (OV) or Extended Validation (EV) Code Signing certificate from a CA. This avoids the “Unknown publisher” message and helps SmartScreen reputation build.

## Generate a self-signed certificate (developer workstation)

1) Create a self-signed cert in your CurrentUser store with Code Signing EKU.
2) Export the certificate with private key to a password-protected .pfx.
3) Export the public certificate to .cer (safe to share/commit).

Store the `.pfx` in `tools/signing/` locally, but do NOT commit it. The `.cer` may be committed (for local trust/testing).

## Local trust for testing (optional)

To eliminate the “Unknown publisher” message on your own machine during testing, import `tools/signing/dev-codesign.cer` into the “Trusted Root Certification Authorities” store (Current User). Do not instruct end users to do this.

## Build with signing

The build scripts accept signing parameters and will timestamp signatures via a TSA. Example parameters (placeholders shown):

- `-SignPfxPath` — path to your .pfx (e.g., `D:\\code\\mc\\tools\\signing\\dev-codesign.pfx`)
- `-SignPfxPassword` — password for the .pfx
- `-TimestampUrl` — e.g., `http://timestamp.digicert.com`

Both the app EXE and installer EXE are signed when these parameters are provided.

## Verifying signatures

- Windows Explorer: Right‑click the EXE → Properties → Digital Signatures.
- Command line (advanced): `signtool verify /pa /v <path-to-exe>`
  - For self‑signed certs, verification may report an untrusted root unless you install the `.cer` into your Trusted Root store locally.

## SmartScreen expectations

- Self‑signed: Signature is present, but SmartScreen will likely still warn users. This is normal.
- Publicly trusted: Users should see your publisher name; SmartScreen warnings decrease as reputation builds or immediately with EV certs.

## Security and repository hygiene

- Never commit private keys or `.pfx` files. `.gitignore` blocks common key formats.
- It’s safe to commit `.cer` (public certificate) for documentation or local trust during testing.
