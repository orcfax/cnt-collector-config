"""Policy IDs per DEX and Smart Contract Addresses per DEX

POLICIES:
Policy IDs for DEXes which have a specific asset (policy id + asset name)
attached to all the UTxOs with listed pairs
Minswap also has a different unique token (same policy id, different asset name)
attached to each UTxO, that's the "policy2" used for.
WingRiders has different addresses for its pairs UTxOs (created using the same
payment key, but with different stake keys).

ADDRESSES:
Addresses for DEXes which have their pairs listed on specific addresses only
SundaeSwap has a unique policy id and unique asset name for each pair,
but it is much faster to identify the DEX pairs UTxOs by looking at the address
than looking for all UTxOs at all addresses where a token with its policy id is present.
Spectrum has 2 smart contract addresses, one for V1, the other for V2. Each pair UTxO
has a different policy id for the security token.
"""

SECURITY_ASSETS = [
    {
        "source": "MinSwap",
        "security_assets": [
            {
                "policy": "0be55d262b29f564998ff81efe21bdc0022621c12f15af08d0f2ddb1",
            },
        ],
    },
    {
        "source": "MinSwapV2",
        "security_assets": [
            {
                "policy": "f5808c2c990d86da54bfc97d89cee6efa20cd8461616359478d96b4c",
            },
        ],
    },
    {
        "source": "SundaeSwapV3",
        "security_assets": [
            {
                "policy": "e0302560ced2fdcbfcb2602697df970cd0d6a38f94b32703f51c312b",
            },
        ],
    },
    {
        "source": "WingRiders",
        "security_assets": [
            {
                "policy": "026a18d04a0c642759bb3d83b12e3344894e5c1c7b2aeb1a2113a570",
                "asset": "4c",
            },
        ],
    },
    {
        "source": "WingRidersV2",
        "security_assets": [
            {
                "policy": "6fdc63a1d71dc2c65502b79baae7fb543185702b12c3c5fb639ed737",
                "asset": "4c",
            },
        ],
    },
    {
        "source": "Snek.fun",
        "security_assets": [
            {
                "policy": "d8eb52caf3289a2880288b23141ce3d2a7025dcf76f26fd5659add06",
            },
        ],
    },
    {
        "source": "Splash",
        "security_assets": [
            {
                "policy": "7a3b08bf74ac6283edf40087f4b53e9b01b0d46a59fee3dd417fda9d",  # ADA-USDM
            },
            {
                "policy": "e73e65176c6bd31dbc878e317e852c826a534fb949d279a463ecbd18",  # STRIKE-ADA
            },
            {
                "policy": "7b5dee4d7c3d06882cd52d659b4822f4366ba402053d0e691f1e1ed4",  # HUNT-ADA
            },
            {
                "policy": "bde0baebb269e9296c9ecdcceeb33fe464361d099b89698470d6b804",  # SPLASH-ADA
            },
            {
                "policy": "50e1fdf5cb92c367afb28445a2ba82c5be351f6300924799c032b5a5",  # SURF-ADA
            },
            {
                "policy": "5cb6e093f8a900f82ad299c807511b9faf2273adbac58cf4a35a4c99",  # rsERG-ADA
            },
            {
                "policy": "ce1a4f1103fca3f93c1ba9b4e87fb0d9e855d66965ca3cf45165824a",  # SNEK-ADA
            },
        ],
    },
    {
        "source": "CSwap",
        "security_assets": [
            {
                "policy": "a3437274f93dfdf36e949a4d9533e964aebde7a1cd229baeca7bdafa",  # ADA-CSWAP
            },
            {
                "policy": "8e50527b8cc1763348b393dca349bf04385ee12d4568afa0c8a457a9",  # SNEK-ADA
            },
            {
                "policy": "a00d48eff61d8cfd86b5795d0b15015b84a33f139f22e7c8e3005c34",  # IAG-ADA
            },
            {
                "policy": "f7e8f4ce8c153b99acbcf201e18c67be2cacd4a0d812458d0d5834bc",  # SURF-ADA
            },
            {
                "policy": "83911d2a8db0a1c307f025c873359a3f2f0c580d5572e3c01f846f6f",  # STRIKE-ADA
            },
            {
                "policy": "c3c6686be48991209904f9652d9e6ba6e2c946429c5d68d0a3dd5792",  # WMTX-ADA
            },
        ],
    },
    {
        "source": "VyFi",
        "security_assets": [
            {
                "policy": "f7f9777979a2a96777823f149e6696954f43967fc56cfc7095a33f98",  # ADA-USDA
            },
            {
                "policy": "3b33dbef13ccf577299a7119f6d57cdef1514e5d488cbc2a44d9c17a",  # ADA-WMTX
            },
            {
                "policy": "60d04ebc9b110ba8690fe79204d23ad7e94f060221fa02d037126ffd",  # ADA-LQ
            },
            {
                "policy": "91273656a81cc90ae6a5403a39052eeae71f17332cc1928be01ec656",  # ADA-IAG
            },
            {
                "policy": "96c31772282e6ae5c629120471c5bbcdef538226b31b97d74c50ca3c",  # ADA-SNEK
            },
        ],
    },
]

ADDRESSES = [
    {
        "source": "SundaeSwap",
        "address": "addr1w9qzpelu9hn45pefc0xr4ac4kdxeswq7pndul2vuj59u8tqaxdznu",
    },
]
