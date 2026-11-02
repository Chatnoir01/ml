"""RAVEN-007: crash-only, single-host local witness vote intent journal.

RESEARCH ONLY. This is NOT a Byzantine consensus implementation or trusted
hardware attestation. A POSIX local filesystem, trusted directory, stable
storage and a crash-only host are assumed. Deleting/replacing/restoring an
older journal, stealing the Ed25519 key or hostile OS control defeats safety.

The *key invariant* is that the witness does not produce an Ed25519
attestation until an irrevocable-under-crash same-parent voting intent has
been recorded, fsync'd and the containing directory fsync'd.

No attempt is made to guarantee fault-tolerance against deliberate disk
rollback, multiple machines sharing a witness key, network filesystems,
snapshot restoration, asynchronous replica divergence, or multiple epochs.
"""
from __future__ import annotations

import errno
from hashlib import sha256
import json
import os
from pathlib import Path
import stat

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from research.raven_fork_evidence import CheckpointReceipt
from research.raven_quorum_model import (
    Attestation, HonestWitness, Roster, _check_root_receipt, sign_witness_claim,
)
from research.raven_signed_model import Rejected, canonical
from research.raven_witness_model import _digest as receipt_id

DOMAIN = "RAVEN-007/crash-only-witness-intent/v1"
SCHEMA = 1
MAX_RECORD_BYTES = 4096


class SimulatedCrash(RuntimeError):
    """A deterministic exception injected at a named durability boundary."""


class FileVoteJournal:
    """One crash-surviving vote intent per pinned parent and witness public key.

    Uses O_CREAT | O_EXCL to atomically choose one parent vote under concurrent
    POSIX processes; fsyncs the record AND directory before permitting signing.
    An unparseable/partial file is an indefinite fail-closed lock, not a permit
    to overwrite a missing receipt. This intentionally prioritizes safety
    over liveness and offers no recovery from a deliberately erased history.
    """

    CRASH_POINTS = (
        "before_create", "after_open", "after_record_fsync",
        "after_directory_fsync", "before_sign", "after_sign",
    )

    def __init__(self, root: Path):
        root = Path(root)
        if root.is_symlink() or not root.is_dir():
            raise Rejected("journal root must be an existing trusted local directory")
        if root.stat().st_mode & 0o022:
            raise Rejected("journal directory must not be group/world-writable")
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise Rejected("required POSIX filesystem guards unavailable")
        self.root = root

    def _identity(self, roster: Roster, witness: str,
                  receipt: CheckpointReceipt) -> dict:
        return {
            "domain": DOMAIN,
            "schema": SCHEMA,
            "witness": witness,
            "witness_public_key": roster.witnesses[witness].public_bytes_raw().hex(),
            "issuer": roster.issuer,
            "namespace": roster.namespace,
            "compartment": roster.compartment,
            "genesis_commitment": roster.genesis_commitment,
            "parent_epoch": receipt.parent_epoch,
            "parent_commitment": receipt.parent_commitment,
        }

    def _path(self, identity: dict) -> Path:
        # The path is a hash of the parent identity, *not* of the child vote.
        # This ensures two conflicting proposed children compete for ONE file.
        return self.root / ("vote-"+sha256(canonical(identity)).hexdigest()+".json")

    @staticmethod
    def _crash(phase: str, crash_at: str | None) -> None:
        if crash_at == phase:
            raise SimulatedCrash(phase)

    def _read_existing(self, path: Path, identity: dict, receipt_hash: str) -> None:
        if path.is_symlink() or not path.is_file():
            raise Rejected("journal vote record missing/invalid file type")
        if path.stat().st_size > MAX_RECORD_BYTES:
            raise Rejected("journal vote record is oversized")
        try:
            raw = path.read_bytes()
            entry = json.loads(raw)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Rejected("journal vote record damaged; fail closed") from exc
        if type(entry) is not dict or set(entry) != {"identity","receipt_hash","sha256"}:
            raise Rejected("journal vote record corrupt; fail closed")
        plain={"identity":identity,"receipt_hash":receipt_hash}
        if (entry.get("identity") != identity
                or entry.get("receipt_hash") != receipt_hash
                or entry.get("sha256") != sha256(canonical(plain)).hexdigest()):
            raise Rejected("journal double vote or corrupted vote; fail closed")
        # The same receipt may be signed again after an ACK loss. Ed25519
        # signing of the same bytes is deterministic, but safety relies only on
        # the persisted same-receipt hash, not deterministic signature bytes.

    def commit_intent(self, roster: Roster, witness: str,
                      receipt: CheckpointReceipt, *,
                      crash_at: str | None = None) -> str:
        if crash_at is not None and crash_at not in self.CRASH_POINTS:
            raise ValueError("unknown injected crash phase")
        if witness not in roster.witnesses:
            raise Rejected("unregistered witness")
        _check_root_receipt(receipt, roster)
        identity=self._identity(roster, witness, receipt)
        chosen_hash=receipt_id(receipt)
        path=self._path(identity)
        self._crash("before_create",crash_at)
        body={"identity":identity,"receipt_hash":chosen_hash}
        record={**body,"sha256":sha256(canonical(body)).hexdigest()}
        raw=canonical(record)+b"\n"
        if len(raw)>MAX_RECORD_BYTES:
            raise Rejected("journal intent larger than maximum")
        try:
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        except FileExistsError:
            self._read_existing(path,identity,chosen_hash)
            return chosen_hash
        except OSError as exc:
            raise Rejected("unable to establish exclusive journal intent") from exc
        try:
            self._crash("after_open",crash_at)
            cursor=0
            while cursor<len(raw):
                written=os.write(fd,raw[cursor:])
                if written<=0:
                    raise OSError("zero-byte durable intent write")
                cursor+=written
            os.fsync(fd)
            self._crash("after_record_fsync",crash_at)
        finally:
            os.close(fd)
        dirfd=None
        try:
            dirfd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            os.fsync(dirfd)
        except OSError as exc:
            raise Rejected("unable to fsync journal directory") from exc
        finally:
            if dirfd is not None:
                os.close(dirfd)
        self._crash("after_directory_fsync",crash_at)
        return chosen_hash


class DurableHonestWitness(HonestWitness):
    """Crash-only local journal integration with the RAVEN-006 quorum model."""

    def __init__(self, witness_id: str, private_key: Ed25519PrivateKey,
                 roster: Roster, journal: FileVoteJournal):
        super().__init__(witness_id,private_key,roster)
        self.journal=journal

    def endorse(self, receipt: CheckpointReceipt, *,
                crash_at: str | None = None) -> Attestation:
        _check_root_receipt(receipt,self.roster)
        self.history.observe(receipt)
        if not self.history.is_rooted(receipt):
            raise Rejected("unrooted witness proposal")
        self.journal.commit_intent(
            self.roster,self.witness_id,receipt,crash_at=crash_at
        )
        FileVoteJournal._crash("before_sign",crash_at)
        att=sign_witness_claim(
            self.private_key,self.roster,self.witness_id,receipt
        )
        FileVoteJournal._crash("after_sign",crash_at)
        self._votes[(receipt.parent_epoch,receipt.parent_commitment)]=att
        return att
