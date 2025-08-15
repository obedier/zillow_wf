import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/config/database';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    
    // Extract search and filter parameters
    const search = searchParams.get('search') || '';
    const minPrice = searchParams.get('minPrice');
    const maxPrice = searchParams.get('maxPrice');
    const minBeds = searchParams.get('minBeds');
    const minBaths = searchParams.get('minBaths');
    const waterfront = searchParams.get('waterfront') || 'all';
    const city = searchParams.get('city') || '';
    const state = searchParams.get('state') || '';
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');
    const offset = (page - 1) * limit;

    // Build the where clause for filtering
    const where: any = {};

    // Search by address, city, or ZPID
    if (search) {
      where.OR = [
        { address: { contains: search, mode: 'insensitive' } },
        { city: { contains: search, mode: 'insensitive' } },
        { zpid: { contains: search, mode: 'insensitive' } },
      ];
    }

    // Filter by city
    if (city) {
      where.city = { contains: city, mode: 'insensitive' };
    }

    // Filter by state
    if (state) {
      where.state = { contains: state, mode: 'insensitive' };
    }

    // Filter by price range
    if (minPrice || maxPrice) {
      where.price = {};
      if (minPrice) where.price.gte = parseInt(minPrice);
      if (maxPrice) where.price.lte = parseInt(maxPrice);
    }

    // Filter by bedrooms
    if (minBeds) {
      where.beds = { gte: parseInt(minBeds) };
    }

    // Filter by bathrooms
    if (minBaths) {
      where.baths = { gte: parseInt(minBaths) };
    }

    // Filter by waterfront status
    if (waterfront === 'waterfront') {
      where.isWaterfront = true;
    } else if (waterfront === 'non-waterfront') {
      where.isWaterfront = false;
    }
    // 'all' and 'with-analysis' don't add waterfront filters

    // Get total count for pagination
    const totalCount = await prisma.listingsSummary.count({ where });

    // Get properties with pagination
    const properties = await prisma.listingsSummary.findMany({
      where,
      include: {
        details: true,
        derived: true,
        wfData: true,
        photos: {
          take: 1, // Just get the first photo for thumbnails
          orderBy: { photoOrder: 'asc' }
        },
        _count: {
          select: {
            photos: true,
            comments: true,
            favorites: true
          }
        }
      },
      orderBy: [
        { createdAt: 'desc' },
        { zpid: 'asc' }
      ],
      skip: offset,
      take: limit,
    });

    // For 'with-analysis' filter, we need to post-filter to only include properties with waterfront analysis
    let filteredProperties = properties;
    if (waterfront === 'with-analysis') {
      filteredProperties = properties.filter(prop => prop.wfData !== null);
    }

    // Transform the data for the frontend
    const transformedProperties = filteredProperties.map(property => ({
      zpid: property.zpid,
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
      mainPhoto: property.photos[0] || null,
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
    }));

    return NextResponse.json({
      success: true,
      data: {
        properties: transformedProperties,
        pagination: {
          page,
          limit,
          total: totalCount,
          totalPages: Math.ceil(totalCount / limit),
          hasNext: page < Math.ceil(totalCount / limit),
          hasPrev: page > 1,
        },
        filters: {
          search,
          minPrice,
          maxPrice,
          minBeds,
          minBaths,
          waterfront,
          city,
          state,
        },
        summary: {
          totalProperties: totalCount,
          propertiesWithAnalysis: await prisma.wfData.count(),
          waterfrontProperties: await prisma.listingsSummary.count({ where: { isWaterfront: true } }),
        }
      }
    });

  } catch (error) {
    console.error('Error fetching properties:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch properties',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
