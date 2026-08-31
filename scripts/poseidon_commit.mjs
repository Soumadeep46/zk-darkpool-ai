import { buildPoseidon } from "circomlibjs";

const [a, b] = process.argv.slice(2);

if (a === undefined || b === undefined) {
  throw new Error("usage: node poseidon_commit.mjs a b");
}

const poseidon = await buildPoseidon();

const F = poseidon.F;

console.log(
  F.toString(
    poseidon([BigInt(a), BigInt(b)])
  )
);