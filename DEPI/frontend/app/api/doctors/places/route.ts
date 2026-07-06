import { NextResponse } from "next/server";

type PlacesSearchBody = {
  specialist?: string;
  lat?: number;
  lng?: number;
  reason?: string;
};

type GooglePlacesResponse = {
  places?: Array<{
    displayName?: { text?: string };
    formattedAddress?: string;
    rating?: number;
    userRatingCount?: number;
    regularOpeningHours?: { openNow?: boolean };
    internationalPhoneNumber?: string;
    googleMapsUri?: string;
    types?: string[];
  }>;
};

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as PlacesSearchBody;
    const { specialist, lat, lng, reason } = body;

    if (
      typeof specialist !== "string" ||
      typeof lat !== "number" ||
      typeof lng !== "number" ||
      typeof reason !== "string"
    ) {
      return NextResponse.json({ error: "Missing fields" }, { status: 400 });
    }

    const response = await fetch("https://places.googleapis.com/v1/places:searchNearby", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": process.env.GOOGLE_PLACES_API_KEY ?? "",
        "X-Goog-FieldMask":
          "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.regularOpeningHours,places.internationalPhoneNumber,places.googleMapsUri,places.types",
      },
      body: JSON.stringify({
        includedTypes: ["doctor", "hospital", "medical_clinic", "physiotherapist"],
        maxResultCount: 5,
        locationRestriction: {
          circle: {
            center: { latitude: lat, longitude: lng },
            radius: 5000,
          },
        },
        rankPreference: "DISTANCE",
      }),
    });

    if (!response.ok) {
      throw new Error("Places request failed");
    }

    const data = (await response.json()) as GooglePlacesResponse;
    const specialistTerms = specialist.toLowerCase().split(/\s+/).filter(Boolean);
    const reasonTerms = reason.toLowerCase().split(/\s+/).filter(Boolean);

    const mappedArray = (data.places ?? [])
      .map((place) => ({
        name: place.displayName?.text ?? "Unknown place",
        address: place.formattedAddress ?? "Address not available",
        rating: place.rating ?? null,
        reviewCount: place.userRatingCount ?? 0,
        phone: place.internationalPhoneNumber ?? null,
        mapsUrl: place.googleMapsUri ?? null,
        isOpen: place.regularOpeningHours?.openNow ?? null,
        source: "google_places" as const,
        types: place.types ?? [],
      }))
      .sort((a, b) => {
        const aHaystack = `${a.name} ${a.address} ${a.types.join(" ")}`.toLowerCase();
        const bHaystack = `${b.name} ${b.address} ${b.types.join(" ")}`.toLowerCase();
        const score = (haystack: string) =>
          specialistTerms.filter((term) => haystack.includes(term)).length * 2 +
          reasonTerms.filter((term) => haystack.includes(term)).length;
        return score(bHaystack) - score(aHaystack);
      })
      .map((doctor) => ({
        name: doctor.name,
        address: doctor.address,
        rating: doctor.rating,
        reviewCount: doctor.reviewCount,
        phone: doctor.phone,
        mapsUrl: doctor.mapsUrl,
        isOpen: doctor.isOpen,
        source: doctor.source,
      }));

    return NextResponse.json({ doctors: mappedArray, specialist, reason });
  } catch {
    return NextResponse.json({ error: "Places search failed" }, { status: 500 });
  }
}
