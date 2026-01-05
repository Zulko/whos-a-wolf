/** Statement classes representing boolean statements about werewolves. */

/** Returns possessive form: "James'" for names ending in s, "John's" otherwise */
function possessive(name) {
  return name.endsWith("s") ? `${name}'` : `${name}'s`;
}

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
   * Convert this statement to localized text (respects current locale).
   * @param {string[]} names - List of villager names, where names[i] is the name of villager i
   * @returns {string} Localized description of this statement
   */
  toEnglish(names) {
    throw new Error("toEnglish must be implemented by subclass");
  }

  /**
   * Convert this statement to French text.
   * @param {string[]} names - List of villager names, where names[i] is the name of villager i
   * @returns {string} French description of this statement
   */
  toFrench(names) {
    // Default implementation: use toEnglish with French locale
    return this.toEnglish(names);
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
    return `${names[this.bIndex]} has always been under ${possessive(
      names[this.aIndex]
    )} spell. If ${names[this.aIndex]} is a werewolf, then so is ${
      names[this.bIndex]
    }.`;
  }

  toFrench(names) {
    return `${names[this.bIndex]} a toujours été sous le l'influence de ${
      names[this.aIndex]
    }. Si ${names[this.aIndex]} est un loup-garou, alors ${
      names[this.bIndex]
    } aussi.`;
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

  toFrench(names) {
    return `${names[this.aIndex]} et ${
      names[this.bIndex]
    } sont inséparables. Soit les deux sont des loups, soit aucun ne l'est.`;
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

  toFrench(names) {
    return `Au moins l'un de ${names[this.aIndex]} et ${
      names[this.bIndex]
    } est un loup : mon Timmy allait les rencontrer la nuit où il a été dévoré.`;
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

  toFrench(names) {
    return `${names[this.aIndex]} et ${
      names[this.bIndex]
    } se haissent avec une telle férocité qu'il est clair que l'un est un loup et l'autre non.`;
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
    } are so unalike! Clearly they couldn't both be wolves.`;
  }

  toFrench(names) {
    return `${names[this.aIndex]} et ${
      names[this.bIndex]
    } sont si différents ! Clairement, ils ne peuvent pas tous les deux être des loups.`;
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

  toFrench(names) {
    return `J'ai vu ${names[this.bIndex]} rôder autour de ${
      names[this.aIndex]
    }. Si ${names[this.aIndex]} n'est pas un loup, alors ${
      names[this.bIndex]
    } en est un.`;
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

  toFrench(names) {
    return `Je connais très bien ${names[this.aIndex]} et ${
      names[this.bIndex]
    } et aucun d'eux n'est un loup.`;
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
        return "The pawprints show these beasts go by pair. There's an even number of wolves among my neighbors.";
      } else {
        return "Wolves hunt by pair but I saw a lone one! There's an odd number of wolves among my neighbors.";
      }
    } else {
      const isSingular = this.count === 1;
      if (this.comparison === "exactly") {
        if (isSingular) {
          return "I counted the pawprints! There is exactly 1 wolf among my neighbors.";
        } else {
          return `I counted the pawprints! There are exactly ${this.count} wolves among my neighbors.`;
        }
      } else if (this.comparison === "at_most") {
        if (isSingular) {
          return "I've seen the wolves, and there is at most 1 of them.";
        } else {
          return `I've seen the wolves, and there are at most ${this.count} of them.`;
        }
      } else {
        // at_least
        if (isSingular) {
          return "I looked at the bite marks. There is at least 1 wolf among my neighbors.";
        } else {
          return `I looked at the bite marks. There are at least ${this.count} wolves among my neighbors.`;
        }
      }
    }
  }

  toFrench(names) {
    if (this._isParity) {
      if (this.count === "even") {
        return "Les empreintes montrent que ces bêtes vont par paires. Il y a un nombre pair de loups parmi mes voisins.";
      } else {
        return "Les loups chassent en duo mais j'en ai vu un solitaire ! Il y a un nombre impair de loups parmi mes voisins.";
      }
    } else {
      const isSingular = this.count === 1;
      if (this.comparison === "exactly") {
        if (isSingular) {
          return "J'ai compté les empreintes! Il y a exactement 1 loup parmi mes voisins.";
        } else {
          return `J'ai compté les empreintes! Il y a exactement ${this.count} loups parmi mes voisins.`;
        }
      } else if (this.comparison === "at_most") {
        if (isSingular) {
          return "J'ai vu les loups, et il y en a au plus 1.";
        } else {
          return `J'ai vu les loups, et il y en a au plus ${this.count}.`;
        }
      } else {
        // at_least
        if (isSingular) {
          return "J'ai étudié les marques de morsure. Il y a au moins 1 loup parmi mes voisins.";
        } else {
          return `J'ai étudié les marques de morsure. Il y a au moins ${this.count} loups parmi mes voisins.`;
        }
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
