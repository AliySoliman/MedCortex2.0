"use client";

import { useEffect, useState } from "react";

type Coordinates = {
  lat: number;
  lng: number;
};

export function useUserLocation() {
  const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
  const [locationAvailable, setLocationAvailable] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !navigator.geolocation) {
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoordinates({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
        setLocationAvailable(true);
      },
      () => {
        setCoordinates(null);
        setLocationAvailable(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    );
  }, []);

  return { coordinates, locationAvailable };
}
