# tema

Multi-provider temporary email CLI with real domains (gmail, outlook, edu).

## Install

```bash
pip install tema
```

For providers behind Cloudflare (emailmux, emailnator, smailpro, privatix):

```bash
pip install tema[cf]
```

## Usage

```bash
# Create temp mailbox (gmail by default)
tema create

# Create with specific domain
tema create -d outlook
tema create -d edu

# Wait for new message
tema wait --timeout 120

# Read latest message
tema read

# Extract links / find verification link
tema links
tema verify

# List all messages
tema list

# List available domains and providers
tema domains
tema providers

# Generate Gmail +alias
tema gmail-alias user@gmail.com
```

## As a library

```python
from tema import create_email, wait_for_message, get_inbox, get_message_body

state = create_email(domain="gmail")
print(state["email"])

msg = wait_for_message(timeout=60)
print(msg["subject"], msg["html"])
```

## Providers

| Provider | Domains | Cloudflare |
|----------|---------|------------|
| emailmux | gmail, googlemail, outlook, hotmail, icloud | yes |
| emailnator | gmail, googlemail | yes |
| smailpro | edu | yes |
| privatix | temp | yes |
| burner | temp | no |
| tempmaili | edu | no |
| etempmail | edu | no |

Providers are tried in priority order with automatic fallback.

## Environment

| Variable | Description |
|----------|-------------|
| `TEMA_STATE_FILE` | Custom path for mailbox state file (default: `./.tema_state.json`) |

## License

MIT
