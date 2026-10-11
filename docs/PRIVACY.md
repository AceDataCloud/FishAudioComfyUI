# Privacy

- Tool nodes send the selected parameters and the process environment's Ace Data Cloud key to `https://api.acedata.cloud` using the published FishAudioDify API contract. Prompts and reference media URLs may be included.
- Read-only task queries use existing IDs; paid actions may consume Credits. Check the current service price and request history before submitting or retrying.
- Native media loaders accept only allowlisted Ace Data Cloud HTTPS CDN hosts, without redirects or credentials.
- The key is never stored in workflow JSON or logs by this package.
