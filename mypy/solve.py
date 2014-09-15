"""Type inference constraint solving"""

from typing import List, Dict

from mypy.types import Type, Void, NoneTyp, AnyType, ErrorType, BasicTypes
from mypy.constraints import Constraint, SUPERTYPE_OF
from mypy.join import join_types
from mypy.meet import meet_types
from mypy.subtypes import is_subtype


def solve_constraints(vars: List[int], constraints: List[Constraint],
                      basic: BasicTypes) -> List[Type]:
    """Solve type constraints.

    Return the most likely type or None if the variable could not be solved. If a variable
    has no constraints, arbitrarily pick NoneTyp as the value of the type variable.
    """
    # Collect a list of constraints for each type variable.
    cmap = Dict[int, List[Constraint]]()
    for con in constraints:
        a = cmap.get(con.type_var, [])
        a.append(con)
        cmap[con.type_var] = a

    res = []  # type: List[Type]

    # Solve each type variable separately.
    for tvar in vars:
        bottom = None  # type: Type
        top = None  # type: Type

        # Process each contraint separely, and calculate the lower and upper
        # bounds based on constraints. Note that we assume that the constraint
        # targets do not have constraint references.
        for c in cmap.get(tvar, []):
            if c.op == SUPERTYPE_OF:
                if bottom is None:
                    bottom = c.target
                else:
                    bottom = join_types(bottom, c.target, basic)
            else:
                if top is None:
                    top = c.target
                else:
                    top = meet_types(top, c.target, basic)

        if isinstance(top, AnyType) or isinstance(bottom, AnyType):
            res.append(AnyType())
            continue
        elif bottom is None:
            if top:
                candidate = top
            else:
                # No constraints for type variable -- type 'None' is the most specific type.
                candidate = NoneTyp()
        elif top is None:
            candidate = bottom
        elif is_subtype(bottom, top):
            candidate = bottom
        else:
            candidate = None
        if isinstance(candidate, ErrorType):
            res.append(None)
        else:
            res.append(candidate)

    return res
