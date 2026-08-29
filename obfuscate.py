import random, sys, os
sys.path.insert(0, os.path.dirname(__file__))

from src.lexer import Lexer
from src.parser import Parser
from src.compiler import Compiler
from src.isa import ISA
from src.serializer import Serializer
from src.name_mangler import NameMangler
from src.anti_tamper import generate_env_check, generate_integrity_check, generate_anti_debug
from src.emitter import emit
from src.cfg_flatten import Flattener

def obfuscate(source: str, seed: int = None, antitamper: bool = False) -> str:
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    rng = random.Random(seed)
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    NameMangler(seed=seed).mangle(ast)
    compiler = Compiler(seed=seed)
    proto = compiler.compile(ast)
    enc_strings = getattr(proto, 'enc_strings', [])
    Flattener(seed=seed).flatten(proto)
    isa = ISA(seed=seed)
    from src.serializer import Serializer
    ser = Serializer(isa, seed)
    blob = ser.dump(proto)
    if antitamper:
        env_check = generate_env_check(rng)
        integrity = generate_integrity_check(blob, rng)
        anti_debug = generate_anti_debug(rng)
    else:
        env_check = '-- (anti-tamper disabled)'
        integrity = '-- (integrity check disabled)'
        anti_debug = '-- (anti-debug disabled)'
    return emit(
        blob=blob, isa=isa, enc_strings=enc_strings,
        env_check=env_check, integrity_check=integrity,
        anti_debug=anti_debug,
        banner=f'Obfuscated by LUOB | seed={seed}',
    )