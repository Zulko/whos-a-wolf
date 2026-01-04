/** Statement classes representing boolean statements about werewolves. */

class Statement {
  /**
   * Create statement from short string representation.
   * @param {string} shortStr - Short string like "I-5-7" or "N-3-4" or "E-0.1.2-2"
   * @returns {Statement} Statement instance
   */
  static fromShortString(shortStr) {
    const parts = shortStr.split("-");
    if (parts.length < 2) {
      throw new Error(`Invalid short string format: ${shortStr}`);
    }

    const code = parts[0];

    // Relationship statements: code-a-b
    if (code === "I") {
      // IfAThenB
      if (parts.length !== 3) {
        throw new Error(`Invalid IfAThenB format: ${shortStr}`);
      }
      return new IfAThenB(parseInt(parts[1]), parseInt(parts[2]));
    } else if (code === "B") {
      // BothOrNeither
      if (parts.length !== 3) {
        throw new Error(`Invalid BothOrNeither format: ${shortStr}`);
      }
      return new BothOrNeither(parseInt(parts[1]), parseInt(parts[2]));
    } else if (code === "A") {
      // AtLeastOne
      if (parts.length !== 3) {
        throw new Error(`Invalid AtLeastOne format: ${shortStr}`);
      }
      return new AtLeastOne(parseInt(parts[1]), parseInt(parts[2]));
    } else if (code === "X") {
      // ExactlyOne
      if (parts.length !== 3) {
        throw new Error(`Invalid ExactlyOne format: ${shortStr}`);
      }
      return new ExactlyOne(parseInt(parts[1]), parseInt(parts[2]));
    } else if (code === "F") {
      // IfNotAThenB
      if (parts.length !== 3) {
        throw new Error(`Invalid IfNotAThenB format: ${shortStr}`);
      }
      return new IfNotAThenB(parseInt(parts[1]), parseInt(parts[2]));
    } else if (code === "T") {
      // AtMostOne
      if (parts.length !== 3) {
        throw new Error(`Invalid AtMostOne format: ${shortStr}`);
      }
      return new AtMostOne(parseInt(parts[1]), parseInt(parts[2]));
    } else if (code === "N") {
      // Neither
      if (parts.length !== 3) {
        throw new Error(`Invalid Neither format: ${shortStr}`);
      }
      return new Neither(parseInt(parts[1]), parseInt(parts[2]));
    }
    // Count statements (all return CountWerewolves)
    else if (code === "E") {
      // Exactly: E-scope-count (scope uses dots)
      if (parts.length !== 3) {
        throw new Error(
          `Invalid CountWerewolves (exactly) format: ${shortStr}`
        );
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      const count = parseInt(parts[2]);
      return new CountWerewolves(scope, count, "exactly");
    } else if (code === "M") {
      // At most: M-scope-count (scope uses dots)
      if (parts.length !== 3) {
        throw new Error(
          `Invalid CountWerewolves (at_most) format: ${shortStr}`
        );
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      const count = parseInt(parts[2]);
      return new CountWerewolves(scope, count, "at_most");
    } else if (code === "L") {
      // At least: L-scope-count (scope uses dots)
      if (parts.length !== 3) {
        throw new Error(
          `Invalid CountWerewolves (at_least) format: ${shortStr}`
        );
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      const count = parseInt(parts[2]);
      return new CountWerewolves(scope, count, "at_least");
    } else if (code === "V") {
      // Even: V-scope (scope uses dots)
      if (parts.length !== 2) {
        throw new Error(`Invalid CountWerewolves (even) format: ${shortStr}`);
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      return new CountWerewolves(scope, "even");
    } else if (code === "O") {
      // Odd: O-scope (scope uses dots)
      if (parts.length !== 2) {
        throw new Error(`Invalid CountWerewolves (odd) format: ${shortStr}`);
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      return new CountWerewolves(scope, "odd");
    } else {
      throw new Error(`Unknown statement code: ${code}`);
    }
  }

  /**
   * Evaluate this statement on a concrete assignment.
   * @param {boolean[]} assignment - Array of booleans representing W[0..N-1]
   * @returns {boolean} True if the statement is satisfied by this assignment
   */
  evaluateOnAssignment(assignment) {
    throw new Error("evaluateOnAssignment must be implemented by subclass");
  }

  /**
   * Convert this statement to English text.
   * @param {string[]} names - List of villager names, where names[i] is the name of villager i
   * @returns {string} English description of this statement
   */
  toEnglish(names) {
    throw new Error("toEnglish must be implemented by subclass");
  }
}

class RelationshipStatement extends Statement {
  constructor(aIndex, bIndex) {
    super();
    this.aIndex = aIndex;
    this.bIndex = bIndex;
  }
}

class CountStatement extends Statement {
  constructor(scopeIndices) {
    super();
    this.scopeIndices = scopeIndices;
  }
}

// Relationship Statement Subclasses

class IfAThenB extends RelationshipStatement {
  /** Semantics: W[a] => W[b] */
  evaluateOnAssignment(assignment) {
    // W[a] => W[b] is equivalent to NOT W[a] OR W[b]
    return !assignment[this.aIndex] || assignment[this.bIndex];
  }

  toEnglish(names) {
    return `${names[this.bIndex]} has always been under ${
      names[this.aIndex]
    }'s spell. If ${names[this.aIndex]} is a werewolf, then so is ${
      names[this.bIndex]
    }.`;
  }
}

class BothOrNeither extends RelationshipStatement {
  /** Semantics: W[a] == W[b] */
  constructor(aIndex, bIndex) {
    // Normalize: always store min(a, b) as a_index, max(a, b) as b_index
    super(Math.min(aIndex, bIndex), Math.max(aIndex, bIndex));
  }

  evaluateOnAssignment(assignment) {
    return assignment[this.aIndex] === assignment[this.bIndex];
  }

  toEnglish(names) {
    return `${names[this.aIndex]} and ${
      names[this.bIndex]
    } are inseparable. Either both are wolves, or neither is.`;
  }
}

class AtLeastOne extends RelationshipStatement {
  /** Semantics: W[a] OR W[b] */
  constructor(aIndex, bIndex) {
    // Normalize: always store min(a, b) as a_index, max(a, b) as b_index
    super(Math.min(aIndex, bIndex), Math.max(aIndex, bIndex));
  }

  evaluateOnAssignment(assignment) {
    return assignment[this.aIndex] || assignment[this.bIndex];
  }

  toEnglish(names) {
    return `At least one of ${names[this.aIndex]} and ${
      names[this.bIndex]
    } is a wolf: my Timmy was going to meet them the night he was eaten.`;
  }
}

class ExactlyOne extends RelationshipStatement {
  /** Semantics: W[a] XOR W[b] (i.e., W[a] != W[b]) */
  constructor(aIndex, bIndex) {
    // Normalize: always store min(a, b) as a_index, max(a, b) as b_index
    super(Math.min(aIndex, bIndex), Math.max(aIndex, bIndex));
  }

  evaluateOnAssignment(assignment) {
    return assignment[this.aIndex] !== assignment[this.bIndex];
  }

  toEnglish(names) {
    return `${names[this.aIndex]} and ${
      names[this.bIndex]
    } hate each other so ferociously, it is clear one is a wolf and the other isn't.`;
  }
}

class AtMostOne extends RelationshipStatement {
  /** Semantics: NOT(W[a] AND W[b]) - at most one of them is a werewolf */
  constructor(aIndex, bIndex) {
    // Normalize: always store min(a, b) as a_index, max(a, b) as b_index
    super(Math.min(aIndex, bIndex), Math.max(aIndex, bIndex));
  }

  evaluateOnAssignment(assignment) {
    // NOT(W[a] AND W[b]) = NOT W[a] OR NOT W[b]
    return !(assignment[this.aIndex] && assignment[this.bIndex]);
  }

  toEnglish(names) {
    return `${names[this.aIndex]} and ${
      names[this.bIndex]
    } behave so differently, at most one of them is a wolf.`;
  }
}

class IfNotAThenB extends RelationshipStatement {
  /** Semantics: (NOT W[a]) => W[b] */
  evaluateOnAssignment(assignment) {
    // (NOT W[a]) => W[b] is equivalent to W[a] OR W[b]
    return assignment[this.aIndex] || assignment[this.bIndex];
  }

  toEnglish(names) {
    return `I have seen ${names[this.bIndex]} creeping on ${
      names[this.aIndex]
    } once. If ${names[this.aIndex]} is not a wolf, then ${
      names[this.bIndex]
    } is a wolf.`;
  }
}

class Neither extends RelationshipStatement {
  /** Semantics: (NOT W[a]) AND (NOT W[b]) */
  constructor(aIndex, bIndex) {
    // Normalize: always store min(a, b) as a_index, max(a, b) as b_index
    super(Math.min(aIndex, bIndex), Math.max(aIndex, bIndex));
  }

  evaluateOnAssignment(assignment) {
    return !assignment[this.aIndex] && !assignment[this.bIndex];
  }

  toEnglish(names) {
    return `I know ${names[this.aIndex]} and ${
      names[this.bIndex]
    } very well, and neither of them is a wolf.`;
  }
}

// Count Statement Subclasses

class CountWerewolves extends CountStatement {
  /**
   * Unified count statement for werewolf constraints.
   *
   * Semantics depend on count and comparison:
   * - count=int, comparison="exactly": SUM(W[i]) == count
   * - count=int, comparison="at_most": SUM(W[i]) <= count
   * - count=int, comparison="at_least": SUM(W[i]) >= count
   * - count="even": SUM(W[i]) % 2 == 0
   * - count="odd": SUM(W[i]) % 2 == 1
   *
   * @param {number[]} scopeIndices - Array of villager indices in the scope
   * @param {number|string} count - Either an int for numeric counts, or "odd"/"even" for parity
   * @param {string} comparison - For int counts: "exactly", "at_most", or "at_least"
   */
  constructor(scopeIndices, count, comparison = "exactly") {
    super(scopeIndices);
    if (typeof count === "string" && count !== "odd" && count !== "even") {
      throw new Error(`count must be int, 'odd', or 'even', got: ${count}`);
    }
    if (
      typeof count === "number" &&
      !["exactly", "at_most", "at_least"].includes(comparison)
    ) {
      throw new Error(
        `comparison must be 'exactly', 'at_most', or 'at_least', got: ${comparison}`
      );
    }
    this.count = count;
    this.comparison = typeof count === "number" ? comparison : null;
  }

  get _isParity() {
    return typeof this.count === "string";
  }

  evaluateOnAssignment(assignment) {
    const werewolfCount = this.scopeIndices.filter((i) => assignment[i]).length;
    if (this._isParity) {
      if (this.count === "even") {
        return werewolfCount % 2 === 0;
      } else {
        // odd
        return werewolfCount % 2 === 1;
      }
    } else {
      if (this.comparison === "exactly") {
        return werewolfCount === this.count;
      } else if (this.comparison === "at_most") {
        return werewolfCount <= this.count;
      } else {
        // at_least
        return werewolfCount >= this.count;
      }
    }
  }

  toEnglish(names) {
    if (this._isParity) {
      if (this.count === "even") {
        return `The pawprints show these beasts go by pair. There's an even number of wolves among my neighbors.`;
      } else {
        return `Wolves hunt by pair but I saw a lone one! There's an odd number of wolves among my neighbors.`;
      }
    } else {
      const plural = this.count !== 1 ? "ves" : "f";
      const verb = this.count !== 1 ? "are" : "is";
      if (this.comparison === "exactly") {
        return `I counted the pawprints! There ${verb} exactly ${this.count} werewol${plural} among my neighbors.`;
      } else if (this.comparison === "at_most") {
        return `I've counted them all, and there ${verb} at most ${this.count} werewol${plural}.`;
      } else {
        // at_least
        return `I saw at least ${this.count} werewol${plural} in the dark last night.`;
      }
    }
  }
}

// Backwards-compatible factory functions for old class names
function ExactlyKWerewolves(scopeIndices, count) {
  return new CountWerewolves(scopeIndices, count, "exactly");
}

function AtMostKWerewolves(scopeIndices, count) {
  return new CountWerewolves(scopeIndices, count, "at_most");
}

function AtLeastKWerewolves(scopeIndices, count) {
  return new CountWerewolves(scopeIndices, count, "at_least");
}

function EvenNumberOfWerewolves(scopeIndices) {
  return new CountWerewolves(scopeIndices, "even");
}

function OddNumberOfWerewolves(scopeIndices) {
  return new CountWerewolves(scopeIndices, "odd");
}

export {
  Statement,
  IfAThenB,
  BothOrNeither,
  AtLeastOne,
  ExactlyOne,
  AtMostOne,
  IfNotAThenB,
  Neither,
  CountWerewolves,
  // Backwards-compatible aliases
  ExactlyKWerewolves,
  AtMostKWerewolves,
  AtLeastKWerewolves,
  EvenNumberOfWerewolves,
  OddNumberOfWerewolves,
};
