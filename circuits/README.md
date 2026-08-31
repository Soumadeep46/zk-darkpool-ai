# Circuits

This directory contains the Circom circuits used for private order validation and trade compatibility verification.

## order_validity.circom

Proves that:

- `price` matches `price_commitment`
- `volume` matches `volume_commitment`
- `MIN_PRICE <= price <= MAX_PRICE`
- `MIN_VOLUME <= volume <= MAX_VOLUME`

The private witness contains:

- `price`
- `volume`
- `price_nonce`
- `volume_nonce`

The public signals are:

- `price_commitment`
- `volume_commitment`

## match_compatibility.circom

Proves that two committed orders satisfy:

- `buy_price >= sell_price`
- `buy_volume == sell_volume`

The exact prices, volumes, and nonces remain private.