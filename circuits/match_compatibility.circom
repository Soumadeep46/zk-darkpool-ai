pragma circom 2.1.6;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";


template MatchCompatibility() {


    signal input buy_price;
    signal input sell_price;

    signal input buy_volume;
    signal input sell_volume;



    signal input buy_price_nonce;
    signal input sell_price_nonce;

    signal input buy_volume_nonce;
    signal input sell_volume_nonce;



    signal input buy_price_commitment;
    signal input sell_price_commitment;

    signal input buy_volume_commitment;
    signal input sell_volume_commitment;



    component buy_price_hash = Poseidon(2);

    buy_price_hash.inputs[0] <== buy_price;
    buy_price_hash.inputs[1] <== buy_price_nonce;

    buy_price_hash.out === buy_price_commitment;



    component sell_price_hash = Poseidon(2);

    sell_price_hash.inputs[0] <== sell_price;
    sell_price_hash.inputs[1] <== sell_price_nonce;

    sell_price_hash.out === sell_price_commitment;



    component buy_volume_hash = Poseidon(2);

    buy_volume_hash.inputs[0] <== buy_volume;
    buy_volume_hash.inputs[1] <== buy_volume_nonce;

    buy_volume_hash.out === buy_volume_commitment;



    component sell_volume_hash = Poseidon(2);

    sell_volume_hash.inputs[0] <== sell_volume;
    sell_volume_hash.inputs[1] <== sell_volume_nonce;

    sell_volume_hash.out === sell_volume_commitment;



    component price_check = GreaterEqThan(32);

    price_check.in[0] <== buy_price;
    price_check.in[1] <== sell_price;

    price_check.out === 1;


    

}


component main {

    public [
        buy_price_commitment,
        sell_price_commitment,
        buy_volume_commitment,
        sell_volume_commitment
    ]

} = MatchCompatibility();