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
    } else if (code === "N") {
      // Neither
      if (parts.length !== 3) {
        throw new Error(`Invalid Neither format: ${shortStr}`);
      }
      return new Neither(parseInt(parts[1]), parseInt(parts[2]));
    }
    // Count statements
    else if (code === "E") {
      // ExactlyKWerewolves: E-scope-count (scope uses dots)
      if (parts.length !== 3) {
        throw new Error(`Invalid ExactlyKWerewolves format: ${shortStr}`);
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      const count = parseInt(parts[2]);
      return new ExactlyKWerewolves(scope, count);
    } else if (code === "M") {
      // AtMostKWerewolves: M-scope-count (scope uses dots)
      if (parts.length !== 3) {
        throw new Error(`Invalid AtMostKWerewolves format: ${shortStr}`);
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      const count = parseInt(parts[2]);
      return new AtMostKWerewolves(scope, count);
    } else if (code === "L") {
      // AtLeastKWerewolves: L-scope-count (scope uses dots)
      if (parts.length !== 3) {
        throw new Error(`Invalid AtLeastKWerewolves format: ${shortStr}`);
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      const count = parseInt(parts[2]);
      return new AtLeastKWerewolves(scope, count);
    } else if (code === "V") {
      // EvenNumberOfWerewolves: V-scope (scope uses dots)
      if (parts.length !== 2) {
        throw new Error(`Invalid EvenNumberOfWerewolves format: ${shortStr}`);
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      return new EvenNumberOfWerewolves(scope);
    } else if (code === "O") {
      // OddNumberOfWerewolves: O-scope (scope uses dots)
      if (parts.length !== 2) {
        throw new Error(`Invalid OddNumberOfWerewolves format: ${shortStr}`);
      }
      const scope = parts[1].split(".").map((x) => parseInt(x));
      return new OddNumberOfWerewolves(scope);
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

class ExactlyKWerewolves extends CountStatement {
  /** Semantics: SUM(W[i] for i in scope) == count */
  constructor(scopeIndices, count) {
    super(scopeIndices);
    this.count = count;
  }

  evaluateOnAssignment(assignment) {
    const werewolfCount = this.scopeIndices.filter((i) => assignment[i]).length;
    return werewolfCount === this.count;
  }

  toEnglish(names) {
    const scopeNames = this.scopeIndices.map((i) => names[i]);
    let scopeDesc;
    if (scopeNames.length === 1) {
      scopeDesc = scopeNames[0];
    } else if (scopeNames.length <= 3) {
      scopeDesc =
        scopeNames.slice(0, -1).join(", ") +
        `, and ${scopeNames[scopeNames.length - 1]}`;
    } else {
      scopeDesc = `${scopeNames.length} villagers`;
    }
    const plural = this.count !== 1 ? "ves" : "f";
    const verb = this.count !== 1 ? "are" : "is";
    return `I counted the pawprints! There ${verb} exactly ${this.count} werewol${plural} among my neighbors.`;
  }
}

class AtMostKWerewolves extends CountStatement {
  /** Semantics: SUM(W[i] for i in scope) <= count */
  constructor(scopeIndices, count) {
    super(scopeIndices);
    this.count = count;
  }

  evaluateOnAssignment(assignment) {
    const werewolfCount = this.scopeIndices.filter((i) => assignment[i]).length;
    return werewolfCount <= this.count;
  }

  toEnglish(names) {
    const scopeNames = this.scopeIndices.map((i) => names[i]);
    let scopeDesc;
    if (scopeNames.length === 1) {
      scopeDesc = scopeNames[0];
    } else if (scopeNames.length <= 3) {
      scopeDesc =
        scopeNames.slice(0, -1).join(", ") +
        `, and ${scopeNames[scopeNames.length - 1]}`;
    } else {
      scopeDesc = `${scopeNames.length} villagers`;
    }
    const plural = this.count !== 1 ? "ves" : "f";
    const verb = this.count !== 1 ? "are" : "is";
    return `I've counted them all, and there ${verb} at most ${this.count} werewol${plural}.`;
  }
}

class AtLeastKWerewolves extends CountStatement {
  /** Semantics: SUM(W[i] for i in scope) >= count */
  constructor(scopeIndices, count) {
    super(scopeIndices);
    this.count = count;
  }

  evaluateOnAssignment(assignment) {
    const werewolfCount = this.scopeIndices.filter((i) => assignment[i]).length;
    return werewolfCount >= this.count;
  }

  toEnglish(names) {
    const scopeNames = this.scopeIndices.map((i) => names[i]);
    let scopeDesc;
    if (scopeNames.length === 1) {
      scopeDesc = scopeNames[0];
    } else if (scopeNames.length <= 3) {
      scopeDesc =
        scopeNames.slice(0, -1).join(", ") +
        `, and ${scopeNames[scopeNames.length - 1]}`;
    } else {
      scopeDesc = `${scopeNames.length} villagers`;
    }
    const plural = this.count !== 1 ? "ves" : "f";
    return `I saw at least ${this.count} werewol${plural} in the dark last night.`;
  }
}

class EvenNumberOfWerewolves extends CountStatement {
  /** Semantics: SUM(W[i] for i in scope) % 2 == 0 */
  evaluateOnAssignment(assignment) {
    const werewolfCount = this.scopeIndices.filter((i) => assignment[i]).length;
    return werewolfCount % 2 === 0;
  }

  toEnglish() {
    return `The pawprints show these beasts go by pair. There's an even number of wolves among my neighbors.`;
  }
}

class OddNumberOfWerewolves extends CountStatement {
  /** Semantics: SUM(W[i] for i in scope) % 2 == 1 */
  evaluateOnAssignment(assignment) {
    const werewolfCount = this.scopeIndices.filter((i) => assignment[i]).length;
    return werewolfCount % 2 === 1;
  }

  toEnglish() {
    return `Wolves hunt by pair but I saw a lone one! There's an odd number of wolves among my neighbors.`;
  }
}

export {
  Statement,
  IfAThenB,
  BothOrNeither,
  AtLeastOne,
  ExactlyOne,
  IfNotAThenB,
  Neither,
  ExactlyKWerewolves,
  AtMostKWerewolves,
  AtLeastKWerewolves,
  EvenNumberOfWerewolves,
  OddNumberOfWerewolves,
};
