db = db.getSiblingDB("RedundantIndex");
db.bar.createIndex({ a: 1, b: -1, c: 1 });
// These indexes are redundant because they are prefixes of the first index.
db.bar.createIndex({ a: 1 });
db.bar.createIndex({ a: -1 });
db.bar.createIndex({ a: 1, b: -1 });
db.bar.createIndex({ a: -1, b: 1 });
db.bar.createIndex({ a: -1, b: 1, c: -1 });
// This is not redundant because of the partial filter expression.
db.bar.createIndex({ a: 1, b: -1 }, { partialFilterExpression: { c: { $gt: 5 } }, name: "partial_index" });
// This is not redundant because of the collation.
db.bar.createIndex({ a: 1, b: -1 }, { collation: { locale: "en", strength: 2 }, name: "collation_index" });
// This is not redundant because of the different order.
db.bar.createIndex({ a: 1, c: 1 });