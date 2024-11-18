# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import base64

import numpy as np
import pytest
import torch

import cuequivariance as cue
import cuequivariance_torch as cuet
from cuequivariance.experimental.e3nn import O3_e3nn

USE_TF32 = False
torch.backends.cuda.matmul.allow_tf32 = USE_TF32
torch.backends.cudnn.allow_tf32 = USE_TF32


@pytest.mark.parametrize("dtype", [torch.float64, torch.float32])
@pytest.mark.parametrize("layout", [cue.ir_mul, cue.mul_ir])
@pytest.mark.parametrize("original_mace", [True, False])
def test_symmetric_contraction(dtype, layout, original_mace):
    mul = 64
    irreps_in = mul * cue.Irreps("O3", "0e + 1o + 2e")
    irreps_out = mul * cue.Irreps("O3", "0e + 1o")

    m = cuet.SymmetricContraction(
        irreps_in,
        irreps_out,
        3,
        5,
        layout_in=layout,
        layout_out=layout,
        dtype=dtype,
        math_dtype=dtype,
        device="cuda",
        original_mace=original_mace,
    )

    Z = 32
    x = torch.randn((Z, irreps_in.dim), dtype=dtype).cuda()
    indices = torch.randint(0, 5, (Z,), dtype=torch.int32).cuda()

    out = m(x, indices)
    assert out.shape == (Z, irreps_out.dim)


def from64(shape: tuple[int, ...], data: str) -> torch.Tensor:
    x = np.frombuffer(base64.b64decode(data), dtype=np.float32).reshape(shape)
    return torch.from_numpy(x.copy()).cuda()


def test_mace_compatibility():
    """Test compatibility with the original MACE implementation.
    To avoid the need to install the original MACE implementation, we use the
    base64-encoded weights and input/output tensors from the original MACE implementation.
    """
    try:
        import e3nn
    except ImportError:
        pytest.skip("e3nn is not installed")

    num_elements = 2
    mul = 4
    irreps_in = cue.Irreps(O3_e3nn, "0e + 1o + 2e")
    irreps_out = cue.Irreps(O3_e3nn, "0e + 1o")

    i = (torch.arange(3) % num_elements).cuda()
    x = from64(
        (3, 36),
        "mHgaP1zHTz5kdhs/3ygQvwzZf77dhoU8+iP+PzzRRD8L9CY+qi9Fv5aiBz/sGJG/xwaev+5w4b2Mbg8+1jDOP4/cwj9rt/u/FedUP7H6qD4y9LM+i7yvPhcifz8coHE/Vkk1PwK0hb/BNig+GF4gP1FNaD94Uj++d+1qPtkrYD8m8o6/9zK9PihGBz9M6Ne9XgCXP/r6bzxTXJO/glIsQPQlDL/fN5w7VeeKP4iYlD/9Msa/GF/cvg+2gz/oRJ6/0Te4P7g+oz8YQ6g+k0q0vN8WEr41/u0/sa55PmAhvD9FZZw/ICJtvyxFkz+zOAq/8JtNPztZX74E9hK/xCdqv4+0Rz9Ah/g+5vmDv6mLL7+M5DI/xgP3PhWEnj5ZmZ0+DBkXwPa12D1mVPo9rDdWP4DkRD+L85Y9EJ01P+8Hiz6gxSM7/eoPwOQOtr8gjge+NBEYPrmg5L2XpO8/F2tCvjEyWL8gjLw+UOIuP5bhPr9qRvM+ADa5v3rqLLwSr/8+PbZhP4tn675SWVm/SMC1P5h/0r0D8v2/CNS7Pza7SL8PqJG+DsKCOpTKoT+xnLg/",
    )

    expected_output = from64(
        (3, 16),
        "pDISvuzVhr9kugO/JNjYvtxQu758ggY+2VL3vl5fbDwAbgA+I48GPUrdO7/ZZpG/bPo8v2AHAzxAxyc8ABY5u0Kfcb5daWc/Pi/0vlZgA0AQtbK+KbnEvhDH2T3LwzC+aOLOvoSKfj8/hNC+8Z5XPXDLez7/0Gk/I6wUv8bBIz9GJshA3BN5Pp3Hi7+UwH0+w7WWPy4YW700E2I+Q42QviR+1jyQW7i+5J0Gvw4Amr/fOim/4jjZPItDgD3kxyI+",
    )

    n_sc = cuet.SymmetricContraction(
        mul * irreps_in,
        mul * irreps_out,
        contraction_degree=3,
        num_elements=num_elements,
        layout_in=cue.ir_mul,
        layout_out=cue.mul_ir,
        original_mace=True,
        device="cuda",
        dtype=torch.float32,
        math_dtype=torch.float64,
    )
    n_sc.weight.data = from64(
        (2, 164 // mul, mul),
        "YiSzvRyt8z1jplo+QeAHPr/bhj0x52a+n5CBvefaVD1GGqk8N7ekvSALfz1mTtG9iuNKu3q2KT5R4T49t/8sPm3Bpzstv809oaaoPSeBmD5o4q+9Ud0YvVBOn72TYSu8BXocvc39dzw653w8+j1YPa/iID1GdXa+Axt4O0O/QD1alhG9hELMvR0wIj1BmyQ+xk+6vJEX5r2xj7K9AtiEvmCkh7w6aP298VwZPIejM7wHIKU+x98IP1Wgrz1QTvG+ayCHPsOKnD6z6Oi+AM6VvcFMiT2UQy6+2C8uPsGyGD+TELG/i/Wkv7g27T71nda+Mxq0vBy/lT2Or3o9NecHPQiSg7uliuY6VqoIPbvkszxoiI27GTIDvYmQlj2PIxi+EvjnOoopmj1F6o894v3NvGUZjrw7NPg7rrdLPMOpjLzCB409Bo5hveKt9ju7u5i8rA2fPdLtu7p6wxE9O+22vbxBiT2XDA09yBkaPUfRnrxO6/q7AC0svFh9Bzvykbw9UBKCvd4BxDyYyw+8J0Ceva+BprzcchE90scMPThbRrwFGDk9CtqcvayFVz3X3Z29LqoIvbu3qjsN+Ak9CRBzvOlP/bwo9jE8x/SWPaIqGj01Jdk9HC2zvHUq+LvvORa9epGwu0WgKz3P/+28kqVivUyiDbw7FiG6wrEEPc7Lir0lAxg8lAj2PL6DnbyI1gq6CcTavQWsnz223zg9TmKrvABjIz1gqme8uXAUO37/Fj03ZcQ9kgsKvZRmnD0llZA9KEjcvRixvTy9UHG+x00FvwgsMr5W42i+j72Yvhluhj6Q4g2+Egn3PbkVq76uIrc+6KsaPnqUl76i9Ma+OzP1vk7E3z43bkw935AAvyndlj0/TBc9ggYMvtSUHj2onBi995SzPG/FCL135xk9xMIjPgVCDr4Xe+888xjtvR0Q4T0wmgg+AOJFPmDQlT2RQGa8CswlveFhbb35yn89t1nTvTPUJD6iHgk+tVyHPA1f+L0OcjG+IYB3PGQ+F71b4IS+HcWwvTmSM70ZXoM9djXpvX+QHL5fIDm8g7NEvPlhNb3JDlK+DKuNvOIcOD1+5wM+t1o7vWEl0r3NyMm7pGErPhD+tr5KlRO/3Kevvl2XDj7bX3g8L54qvhnfyj5z4Le+692ePs1J6j5bZSO+nf6Avsdr4T1cOLq+hZGzPFu0Jj/mBpA94uxRvcuTvbyyzhM7cb/PPGQywTzoo4W9ZZXyvCNH+TsgdYY9XfKmvFQGgjwDTMM9/d4dPQVaFT2NtCC9nr2huw7bp7uU6/y64miBPdy8EjtSSYU9yBo0vNSZDDyuLEM9wx4TPVRMC7uIyx28jK8gPbHXAj0YHX+8NyGNvPjXxL1rEou8GExsvRJJNL2U3Vg8mnlSvE6cyLxmfIW7woQnPeieMD00hV89IquevZjJgD2SKdo8bzknvXcNMT2mtDw8I6ZnvR7SXL3SbpA8gDVgvVCOML0lLCq8ThO+PY6JiL1RLaU7hv7TvM8uJL3Dusg8DLPDPF0r97wQ9wM9WAGBPN0CCj1m1Yu8FLqHPBWUsL3+9kA8/gKlve6jZDuAsTe8hJ2DPc8zMz3VvsK7KbN5vCGFoT2GMyK93W3ZPe5XfT3t+o48zM5jPQMMVTxVJbc9YUG+PRbAxz3f7Is+P8CBPQcNb77TtrM7uXkQvWPMJj6om3K8pCURv4EAQj0Raug9c1e2vU1SpL5QNzg+HLjKvg1Oqz6yrsY+f5N+Pg==",
    )
    output = n_sc(x, i)

    torch.testing.assert_close(output, expected_output, atol=1e-5, rtol=1e-5)