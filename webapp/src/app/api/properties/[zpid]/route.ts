import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/config/database';

export async function GET(
  request: NextRequest,
  { params }: { params: { zpid: string } }
) {
  try {
    const { zpid } = params;

    // Get the property with all related data
    const property = await prisma.listingsSummary.findUnique({
      where: { zpid },
      include: {
        details: true,
        derived: true,
        wfData: true,
        photos: {
          orderBy: { photoOrder: 'asc' }
        },
        textContent: {
          orderBy: { createdAt: 'desc' }
        },
        _count: {
          select: {
            photos: true,
            comments: true,
            favorites: true
          }
        }
      }
    });

    if (!property) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Property not found' 
        },
        { status: 404 }
      );
    }

    // Transform the data for the frontend
    const transformedProperty = {
      zpid: property.zpid,
      url: property.url,
      address: property.address,
      city: property.city,
      state: property.state,
      county: property.county,
      zipCode: property.zipCode,
      price: property.price,
      priceFormatted: property.dPriceFormatted,
      beds: property.beds,
      baths: property.baths,
      homeSizeSqft: property.homeSizeSqft,
      yearBuilt: property.yearBuilt,
      isCondo: property.isCondo,
      isWaterfront: property.isWaterfront,
      pricePerSqft: property.pricePerSqft,
      hoaFee: property.hoaFee,
      latitude: property.latitude,
      longitude: property.longitude,
      zestimate: property.zestimate,
      rentZestimate: property.rentZestimate,
      monthlyHoaFee: property.monthlyHoaFee,
      lotAreaValue: property.lotAreaValue,
      lotAreaUnit: property.lotAreaUnit,
      daysOnZillow: property.daysOnZillow,
      pageViewCount: property.pageViewCount,
      favoriteCount: property.favoriteCount,
      homeStatus: property.homeStatus,
      contingentType: property.contingentType,
      mlsId: property.mlsId,
      mlsName: property.mlsName,
      homeType: property.homeType,
      waterfrontFootage: property.waterfrontFootage,
      dockInfo: property.dockInfo,
      createdAt: property.createdAt,
      updatedAt: property.updatedAt,
      
      // Related data
      details: property.details,
      derived: property.derived,
      wfData: property.wfData,
      photos: property.photos,
      textContent: property.textContent,
      
      // Counts
      photoCount: property._count.photos,
      commentCount: property._count.comments,
      favoriteCount: property._count.favorites,
      
      // Computed fields
      hasWaterfrontAnalysis: property.wfData !== null,
      waterfrontLength: property.derived?.waterfrontLengthFt,
      hasBoatDock: property.derived?.hasBoatDock,
      hasBoatLift: property.derived?.hasBoatLift,
      hasBoatRamp: property.derived?.hasBoatRamp,
      hasMarinaAccess: property.derived?.hasMarinaAccess,
      
      // Waterfront analysis details
      waterfrontAnalysis: property.wfData ? {
        waterfrontLength: property.wfData.waterfrontLength,
        waterType: property.wfData.waterType,
        accessType: property.wfData.accessType,
        analysisDate: property.wfData.analysisDate,
      } : null,
      
      // Derived analysis details
      derivedAnalysis: property.derived ? {
        waterfrontLengthFt: property.derived.waterfrontLengthFt,
        hasBoatDock: property.derived.hasBoatDock,
        hasBoatLift: property.derived.hasBoatLift,
        hasBoatRamp: property.derived.hasBoatRamp,
        hasMarinaAccess: property.derived.hasMarinaAccess,
        bridgeHeightFt: property.derived.bridgeHeightFt,
        waterDepthFt: property.derived.waterDepthFt,
        canalWidthFt: property.derived.canalWidthFt,
        waterTypePrimary: property.derived.waterTypePrimary,
        waterTypeSecondary: property.derived.waterTypeSecondary,
        pricePerWaterfrontFoot: property.derived.pricePerWaterfrontFoot,
        pricePerBuildingSqft: property.derived.pricePerBuildingSqft,
        pricePerLotSqft: property.derived.pricePerLotSqft,
        analysisConfidence: property.derived.analysisConfidence,
        analysisMethod: property.derived.analysisMethod,
        analysisNotes: property.derived.analysisNotes,
      } : null,
    };

    return NextResponse.json({
      success: true,
      data: transformedProperty
    });

  } catch (error) {
    console.error('Error fetching property:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch property',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
