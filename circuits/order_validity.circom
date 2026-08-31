pragma circom 2.1.6;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";


template OrderValidity() {
    signal input price;
    signal input volume;

    signal input price_nonce;
    signal input volume_nonce;

    signal input price_commitment;
    signal input volume_commitment;

    component price_hash = Poseidon(2);
    price_hash.inputs[0] <== price;
    price_hash.inputs[1] <== price_nonce;

    price_hash.out === price_commitment;

    component volume_hash = Poseidon(2);
    volume_hash.inputs[0] <== volume;
    volume_hash.inputs[1] <== volume_nonce;

    volume_hash.out === volume_commitment;

    var MIN_PRICE = 1;
    var MAX_PRICE = 1000000;

    var MIN_VOLUME = 1;
    var MAX_VOLUME = 1000000;

    component price_min_check = GreaterEqThan(32);
    price_min_check.in[0] <== price;
    price_min_check.in[1] <== MIN_PRICE;
    price_min_check.out === 1;

    component price_max_check = LessEqThan(32);
    price_max_check.in[0] <== price;
    price_max_check.in[1] <== MAX_PRICE;
    price_max_check.out === 1;

    component volume_min_check = GreaterEqThan(32);
    volume_min_check.in[0] <== volume;
    volume_min_check.in[1] <== MIN_VOLUME;
    volume_min_check.out === 1;

    component volume_max_check = LessEqThan(32);
    volume_max_check.in[0] <== volume;
    volume_max_check.in[1] <== MAX_VOLUME;
    volume_max_check.out === 1;
}


component main {
    public [
        price_commitment,
        volume_commitment
    ]
} = OrderValidity();